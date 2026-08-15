"""
test_firebase.py — Quick test to verify Firebase connection and write.
Run with: python test_firebase.py
"""

from config import Config
from firestore import FirestoreManager
from scraper import Lead

print("\n=== Firebase Write Test ===\n")

# Load config (reads .env for credentials)
config = Config()

# Connect to Firestore
db = FirestoreManager(
    credentials_file=config.FIREBASE_CREDENTIALS_FILE,
    collection_name=config.FIRESTORE_COLLECTION,
)

# Two dummy leads
dummy_leads = [
    Lead(
        name="Clean Schema Test One",
        phone="9988776655",
        area="Sector 5, Gurugram",
        state="Haryana",
        source="Google Map",
        status="Not Contacted",
    ),
    Lead(
        name="Clean Schema Test Two",
        phone="9988776644",
        area="Sector 6, Faridabad",
        state="Haryana",
        source="Google Map",
        status="Not Contacted",
    ),
]

print(f"Sample Document Schema being sent:")
print(f"  {FirestoreManager._lead_to_dict(dummy_leads[0])}")
print("-" * 50)

result = db.add_leads(dummy_leads)

print(f"\nResult:")
print(f"  Total submitted : {result['total']}")
print(f"  Added to DB     : {result['added']}")
print(f"  Duplicates skip : {result['duplicates']}")

if result["added"] > 0:
    print("\n[SUCCESS] Entries saved to Firebase!")
    print(f"  Check Firebase Console -> Firestore -> '{config.FIRESTORE_COLLECTION}'")
else:
    print("\n[INFO] No new entries added (may already exist as duplicates).")

print("\n=== Test Complete ===\n")
