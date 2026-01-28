import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from backend.models.saved import Collection, SavedBusiness

DATA_DIR = Path(__file__).parent.parent.parent / "data"
COLLECTIONS_FILE = DATA_DIR / "collections.json"
SAVED_BUSINESSES_FILE = DATA_DIR / "saved_businesses.json"


def _load_collections() -> List[Dict]:
    if not COLLECTIONS_FILE.exists():
        return []
    with open(COLLECTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_collections(collections: List[Dict]):
    COLLECTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COLLECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(collections, f, indent=2, ensure_ascii=False)


def _load_saved_businesses() -> List[Dict]:
    if not SAVED_BUSINESSES_FILE.exists():
        return []
    with open(SAVED_BUSINESSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_saved_businesses(saved_businesses: List[Dict]):
    SAVED_BUSINESSES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SAVED_BUSINESSES_FILE, "w", encoding="utf-8") as f:
        json.dump(saved_businesses, f, indent=2, ensure_ascii=False)


def _get_next_collection_id() -> int:
    collections = _load_collections()
    if not collections:
        return 1
    return max(c["collectionId"] for c in collections) + 1


def _get_next_saved_id() -> int:
    saved_businesses = _load_saved_businesses()
    if not saved_businesses:
        return 1
    return max(s["savedId"] for s in saved_businesses) + 1


# Collection Management
def create_collection(user_id: int, name: str) -> Dict:
    """Create a new collection for a user."""
    collections = _load_collections()

    # Check if collection name already exists for this user
    if any(c["userId"] == user_id and c["name"].lower() == name.lower() for c in collections):
        raise ValueError(f"Collection '{name}' already exists")

    collection = Collection(
        collectionId=_get_next_collection_id(),
        userId=user_id,
        name=name,
        createdAt=datetime.utcnow().isoformat()
    )

    collections.append(collection.model_dump())
    _save_collections(collections)
    return collection.model_dump()


def get_user_collections(user_id: int) -> List[Dict]:
    """Get all collections for a user."""
    collections = _load_collections()
    return [c for c in collections if c["userId"] == user_id]


def delete_collection(user_id: int, collection_id: int) -> bool:
    """Delete a collection and all saved businesses in it."""
    collections = _load_collections()
    saved_businesses = _load_saved_businesses()

    # Find and remove the collection
    collection_found = False
    updated_collections = []
    for c in collections:
        if c["collectionId"] == collection_id and c["userId"] == user_id:
            collection_found = True
        else:
            updated_collections.append(c)

    if not collection_found:
        return False

    # Remove all saved businesses in this collection
    updated_saved = [s for s in saved_businesses if s["collectionId"] != collection_id]

    _save_collections(updated_collections)
    _save_saved_businesses(updated_saved)
    return True


def rename_collection(user_id: int, collection_id: int, new_name: str) -> bool:
    """Rename a collection."""
    collections = _load_collections()

    # Check if new name already exists for this user
    if any(c["userId"] == user_id and c["name"].lower() == new_name.lower() and c["collectionId"] != collection_id for c in collections):
        raise ValueError(f"Collection '{new_name}' already exists")

    for c in collections:
        if c["collectionId"] == collection_id and c["userId"] == user_id:
            c["name"] = new_name
            _save_collections(collections)
            return True

    return False


# Saved Business Management
def save_business(user_id: int, business_id: int, collection_id: int) -> Dict:
    """Save a business to a collection."""
    collections = _load_collections()
    saved_businesses = _load_saved_businesses()

    # Verify collection exists and belongs to user
    if not any(c["collectionId"] == collection_id and c["userId"] == user_id for c in collections):
        raise ValueError("Collection not found or does not belong to user")

    # Check if business is already saved in this collection
    if any(s["userId"] == user_id and s["businessId"] == business_id and s["collectionId"] == collection_id for s in saved_businesses):
        raise ValueError("Business already saved in this collection")

    saved = SavedBusiness(
        savedId=_get_next_saved_id(),
        userId=user_id,
        businessId=business_id,
        collectionId=collection_id,
        dateSaved=datetime.utcnow().isoformat()
    )

    saved_businesses.append(saved.model_dump())
    _save_saved_businesses(saved_businesses)
    return saved.model_dump()


def unsave_business(user_id: int, business_id: int, collection_id: Optional[int] = None) -> bool:
    """
    Remove a business from saved.
    If collection_id is provided, remove only from that collection.
    If collection_id is None, remove from all collections.
    """
    saved_businesses = _load_saved_businesses()

    updated_saved = []
    removed = False

    for s in saved_businesses:
        if s["userId"] == user_id and s["businessId"] == business_id:
            if collection_id is None or s["collectionId"] == collection_id:
                removed = True
                continue
        updated_saved.append(s)

    if removed:
        _save_saved_businesses(updated_saved)

    return removed


def get_saved_businesses(user_id: int, collection_id: Optional[int] = None) -> List[Dict]:
    """
    Get saved businesses for a user.
    If collection_id is provided, get only from that collection.
    Otherwise, get from all collections.
    """
    saved_businesses = _load_saved_businesses()

    if collection_id is not None:
        return [s for s in saved_businesses if s["userId"] == user_id and s["collectionId"] == collection_id]
    else:
        return [s for s in saved_businesses if s["userId"] == user_id]


def is_business_saved(user_id: int, business_id: int) -> Dict:
    """
    Check if a business is saved by the user.
    Returns {"saved": bool, "collections": [collection_ids]}
    """
    saved_businesses = _load_saved_businesses()

    user_saved = [s for s in saved_businesses if s["userId"] == user_id and s["businessId"] == business_id]

    return {
        "saved": len(user_saved) > 0,
        "collections": [s["collectionId"] for s in user_saved]
    }


def move_business_to_collection(user_id: int, business_id: int, old_collection_id: int, new_collection_id: int) -> bool:
    """Move a saved business from one collection to another."""
    collections = _load_collections()
    saved_businesses = _load_saved_businesses()

    # Verify new collection exists and belongs to user
    if not any(c["collectionId"] == new_collection_id and c["userId"] == user_id for c in collections):
        raise ValueError("Target collection not found or does not belong to user")

    # Check if business is already in the new collection
    if any(s["userId"] == user_id and s["businessId"] == business_id and s["collectionId"] == new_collection_id for s in saved_businesses):
        raise ValueError("Business already exists in target collection")

    # Update the collection_id
    found = False
    for s in saved_businesses:
        if s["userId"] == user_id and s["businessId"] == business_id and s["collectionId"] == old_collection_id:
            s["collectionId"] = new_collection_id
            found = True
            break

    if found:
        _save_saved_businesses(saved_businesses)

    return found


def get_collection_stats(user_id: int) -> List[Dict]:
    """Get statistics for each collection (name, count of businesses)."""
    collections = get_user_collections(user_id)
    saved_businesses = _load_saved_businesses()

    stats = []
    for collection in collections:
        count = sum(1 for s in saved_businesses if s["collectionId"] == collection["collectionId"])
        stats.append({
            "collectionId": collection["collectionId"],
            "name": collection["name"],
            "count": count,
            "createdAt": collection["createdAt"]
        })

    return stats
