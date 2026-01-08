"""
Firebase Configuration for FTC Insight

This module handles Firebase initialization and provides access to Firestore.
"""

import os
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client

# Global Firestore client
_db: Optional[Client] = None


def get_firestore_client() -> Client:
    """
    Get or initialize the Firestore client
    
    The Firebase credentials should be set via:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to service account JSON
    2. Or FIREBASE_SERVICE_ACCOUNT_JSON containing the JSON directly
    """
    global _db
    
    if _db is not None:
        return _db
    
    try:
        # Check if Firebase app is already initialized
        firebase_admin.get_app()
    except ValueError:
        # Not initialized, initialize now
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        cred_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        elif cred_json:
            import json
            cred = credentials.Certificate(json.loads(cred_json))
        else:
            # Use default credentials (for local development with gcloud auth)
            cred = credentials.ApplicationDefault()
        
        firebase_admin.initialize_app(cred)
    
    _db = firestore.client()
    return _db


def get_collection(collection_name: str):
    """Get a Firestore collection reference"""
    db = get_firestore_client()
    return db.collection(collection_name)


# Collection names
COLLECTIONS = {
    "teams": "teams",
    "team_years": "team_years",
    "events": "events",
    "matches": "matches",
    "team_events": "team_events",
    "team_matches": "team_matches",
    "years": "years",
    "rankings": "rankings",
    "metadata": "metadata",
}
