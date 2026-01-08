"""
Firestore Storage Operations

Read/write operations for storing FTC Insight data in Firestore.
"""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from google.cloud.firestore import Client, WriteBatch
from src.firebase.config import get_firestore_client, COLLECTIONS


def batch_write(collection_name: str, documents: List[Dict[str, Any]], id_field: str = "id") -> int:
    """
    Batch write documents to a Firestore collection with rate limiting
    
    Args:
        collection_name: Name of the collection
        documents: List of document dictionaries
        id_field: Field to use as document ID (default: "id")
    
    Returns:
        Number of documents written
    """
    if not documents:
        return 0
    
    db = get_firestore_client()
    collection = db.collection(collection_name)
    
    # Smaller batch size to avoid quota issues
    batch_size = 200
    total_written = 0
    
    for i in range(0, len(documents), batch_size):
        batch = db.batch()
        chunk = documents[i:i + batch_size]
        
        for doc in chunk:
            doc_id = str(doc.get(id_field, doc.get("key", doc.get("team"))))
            # Add timestamp
            doc["_updated_at"] = datetime.utcnow().isoformat()
            doc_ref = collection.document(doc_id)
            batch.set(doc_ref, doc, merge=True)
        
        # Retry logic with exponential backoff
        max_retries = 5
        for attempt in range(max_retries):
            try:
                batch.commit()
                total_written += len(chunk)
                break
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s, 4s, 8s
                    print(f"  Rate limited, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise
        
        # Small delay between batches to avoid hitting rate limits
        if i + batch_size < len(documents):
            time.sleep(0.2)
    
    return total_written


def write_document(collection_name: str, doc_id: str, data: Dict[str, Any]) -> bool:
    """Write a single document to Firestore"""
    db = get_firestore_client()
    data["_updated_at"] = datetime.utcnow().isoformat()
    db.collection(collection_name).document(doc_id).set(data, merge=True)
    return True


def read_document(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Read a single document from Firestore"""
    db = get_firestore_client()
    doc = db.collection(collection_name).document(doc_id).get()
    return doc.to_dict() if doc.exists else None


def read_collection(collection_name: str, filters: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
    """
    Read documents from a collection with optional filters
    
    Args:
        collection_name: Name of the collection
        filters: List of (field, operator, value) tuples for filtering
    
    Returns:
        List of document dictionaries
    """
    db = get_firestore_client()
    query = db.collection(collection_name)
    
    if filters:
        for field, operator, value in filters:
            query = query.where(field, operator, value)
    
    docs = query.stream()
    return [doc.to_dict() for doc in docs]


def delete_collection(collection_name: str) -> int:
    """Delete all documents in a collection"""
    db = get_firestore_client()
    collection = db.collection(collection_name)
    
    deleted = 0
    batch_size = 500
    
    while True:
        docs = collection.limit(batch_size).stream()
        doc_list = list(docs)
        
        if not doc_list:
            break
        
        batch = db.batch()
        for doc in doc_list:
            batch.delete(doc.reference)
            deleted += 1
        batch.commit()
    
    return deleted


# Specialized write functions for each data type

def write_teams(teams: List[Dict[str, Any]]) -> int:
    """Write team data to Firestore"""
    return batch_write(COLLECTIONS["teams"], teams, id_field="team")


def write_team_years(team_years: List[Dict[str, Any]]) -> int:
    """Write team year data to Firestore"""
    # Create composite key: team_year
    for ty in team_years:
        ty["id"] = f"{ty['team']}_{ty['year']}"
    return batch_write(COLLECTIONS["team_years"], team_years, id_field="id")


def write_events(events: List[Dict[str, Any]]) -> int:
    """Write event data to Firestore"""
    return batch_write(COLLECTIONS["events"], events, id_field="key")


def write_matches(matches: List[Dict[str, Any]]) -> int:
    """Write match data to Firestore"""
    return batch_write(COLLECTIONS["matches"], matches, id_field="key")


def write_team_events(team_events: List[Dict[str, Any]]) -> int:
    """Write team-event data to Firestore"""
    for te in team_events:
        te["id"] = f"{te['team']}_{te['event']}"
    return batch_write(COLLECTIONS["team_events"], team_events, id_field="id")


def write_team_matches(team_matches: List[Dict[str, Any]]) -> int:
    """Write team-match data to Firestore"""
    for tm in team_matches:
        tm["id"] = f"{tm['team']}_{tm['match']}"
    return batch_write(COLLECTIONS["team_matches"], team_matches, id_field="id")


def write_year(year_data: Dict[str, Any]) -> bool:
    """Write year statistics to Firestore"""
    return write_document(COLLECTIONS["years"], str(year_data["year"]), year_data)


def write_rankings(event_key: str, rankings: List[Dict[str, Any]]) -> int:
    """Write event rankings to Firestore"""
    for r in rankings:
        r["event"] = event_key
        r["id"] = f"{event_key}_{r['team']}"
    return batch_write(COLLECTIONS["rankings"], rankings, id_field="id")


def write_metadata(key: str, data: Dict[str, Any]) -> bool:
    """Write metadata (last update times, etc.)"""
    return write_document(COLLECTIONS["metadata"], key, data)


def read_metadata(key: str) -> Optional[Dict[str, Any]]:
    """Read metadata"""
    return read_document(COLLECTIONS["metadata"], key)


# Read functions

def read_teams(year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Read all teams, optionally filtered by active year"""
    if year:
        return read_collection(COLLECTIONS["teams"], [("active", "==", True)])
    return read_collection(COLLECTIONS["teams"])


def read_team_years(year: int) -> List[Dict[str, Any]]:
    """Read team years for a specific year"""
    return read_collection(COLLECTIONS["team_years"], [("year", "==", year)])


def read_events(year: int) -> List[Dict[str, Any]]:
    """Read events for a specific year"""
    return read_collection(COLLECTIONS["events"], [("year", "==", year)])


def read_event(event_key: str) -> Optional[Dict[str, Any]]:
    """Read a single event"""
    return read_document(COLLECTIONS["events"], event_key)


def read_matches(event_key: str) -> List[Dict[str, Any]]:
    """Read matches for an event"""
    return read_collection(COLLECTIONS["matches"], [("event", "==", event_key)])


def read_year(year: int) -> Optional[Dict[str, Any]]:
    """Read year statistics"""
    return read_document(COLLECTIONS["years"], str(year))
