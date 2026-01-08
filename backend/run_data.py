#!/usr/bin/env python3
"""
FTC Insight Data Runner

Main entry point for running the FTC data pipeline.
This script fetches all data from the FTC Events API, calculates statistics,
and stores everything in Firebase Firestore.

Usage:
    # Process all recent seasons (2022-2024)
    python run_data.py
    
    # Process a specific season
    python run_data.py --season 2024
    
    # Process multiple seasons
    python run_data.py --season 2023 --season 2024
    
    # Full refresh (ignore cache)
    python run_data.py --no-cache
    
    # Update current season only
    python run_data.py --update
"""

import sys
import os
import argparse

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def main():
    parser = argparse.ArgumentParser(description='FTC Insight Data Pipeline')
    parser.add_argument(
        '--season', '-s',
        type=int,
        action='append',
        help='Season year to process (can be specified multiple times)'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable API response caching'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Only update current season'
    )
    parser.add_argument(
        '--test-api',
        action='store_true',
        help='Test FTC API connection'
    )
    parser.add_argument(
        '--test-firestore',
        action='store_true',
        help='Test Firestore connection'
    )
    
    args = parser.parse_args()
    
    if args.test_api:
        test_ftc_api()
        return
    
    if args.test_firestore:
        test_firestore()
        return
    
    # Import pipeline after args parsed (for faster --help)
    from src.data.ftc_pipeline import process_season, process_all_seasons, update_current_season
    
    if args.update:
        print("Updating current season...")
        result = update_current_season(cache=not args.no_cache)
        print(f"Update complete: {result}")
    elif args.season:
        for season in args.season:
            print(f"\nProcessing season {season}...")
            result = process_season(season, cache=not args.no_cache)
            print(f"Season {season} complete: {result.get('team_years', 0)} teams processed")
    else:
        print("Processing all recent seasons (2022-2024)...")
        results = process_all_seasons(2022, 2024, cache=not args.no_cache)
        print(f"\nAll seasons complete!")
        for r in results:
            if 'error' not in r:
                print(f"  Season {r['season']}: {r.get('team_years', 0)} teams")


def test_ftc_api():
    """Test FTC API connection"""
    print("Testing FTC API connection...")
    
    from src.ftc_api.read_ftc import get_api_status, get_teams, get_events
    
    # Test API status
    status = get_api_status(cache=False)
    if status:
        print(f"✓ API Status: {status}")
    else:
        print("✗ Failed to get API status")
        return
    
    # Test teams endpoint
    teams = get_teams(2024, cache=False)
    print(f"✓ Teams: Found {len(teams)} teams for 2024")
    
    # Test events endpoint
    events, _ = get_events(2024, cache=False)
    print(f"✓ Events: Found {len(events)} events for 2024")
    
    print("\nFTC API connection successful!")


def test_firestore():
    """Test Firestore connection"""
    print("Testing Firestore connection...")
    
    try:
        from src.firebase.config import get_firestore_client, COLLECTIONS
        from src.firebase.storage import write_document, read_document
        
        # Initialize client
        db = get_firestore_client()
        print("✓ Firestore client initialized")
        
        # Test write
        test_data = {"test": True, "message": "Hello from FTC Insight!"}
        write_document(COLLECTIONS["metadata"], "test", test_data)
        print("✓ Test document written")
        
        # Test read
        result = read_document(COLLECTIONS["metadata"], "test")
        if result and result.get("test"):
            print("✓ Test document read successfully")
        else:
            print("✗ Failed to read test document")
        
        print("\nFirestore connection successful!")
        
    except Exception as e:
        print(f"✗ Firestore error: {e}")
        print("\nMake sure you have:")
        print("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("2. Or created a Firebase service account JSON file")
        print("3. Enabled Firestore in your Firebase project")


if __name__ == '__main__':
    main()
