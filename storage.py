"""Saved-recipe storage, backed by MongoDB.

Kept separate from main.py so the Gemini logic doesn't have to know about the
database. Connects lazily on first use, which means .env is already loaded and
the app still boots (and /recipe still works) when MONGODB_URI isn't set.
"""

import os
import secrets
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

DB_NAME = os.environ.get("MONGODB_DB", "barista")
COLLECTION_NAME = "saved_recipes"

# Length of the public id that ends up in the share URL. 8 random bytes is
# ~11 url-safe characters — short enough to paste, long enough not to guess.
ID_BYTES = 8

_collection = None


class StorageUnavailable(RuntimeError):
    """No database configured, or we couldn't reach it."""


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise StorageUnavailable(
            "Saving is turned off: no MONGODB_URI is configured on the server."
        )

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _collection = client[DB_NAME][COLLECTION_NAME]
    except PyMongoError as e:
        raise StorageUnavailable(f"Couldn't connect to the database: {e}")

    return _collection


def new_id() -> str:
    return secrets.token_urlsafe(ID_BYTES)


def ping() -> dict:
    """Confirm we can actually reach the database. Raises StorageUnavailable."""
    collection = _get_collection()

    try:
        collection.database.client.admin.command("ping")
        saved = collection.count_documents({})
    except PyMongoError as e:
        raise StorageUnavailable(f"Couldn't reach the database: {e}")

    return {"database": DB_NAME, "collection": COLLECTION_NAME, "saved_recipes": saved}


def save(*, order: str, drink_name: str, prep_time: str | None, recipe: str) -> str:
    """Store one recipe and return the id used in its share URL."""
    collection = _get_collection()

    document = {
        "order": order,
        "drink_name": drink_name,
        "prep_time": prep_time,
        "recipe": recipe,
        "created_at": datetime.now(timezone.utc),
    }

    # A collision is vanishingly unlikely, but retrying is cheap.
    for _ in range(5):
        recipe_id = new_id()
        try:
            collection.insert_one({"_id": recipe_id, **document})
            return recipe_id
        except DuplicateKeyError:
            continue
        except PyMongoError as e:
            raise StorageUnavailable(f"Couldn't save the recipe: {e}")

    raise StorageUnavailable("Couldn't allocate an id for the recipe.")


def load(recipe_id: str) -> dict | None:
    """Fetch a saved recipe, or None if that id was never used."""
    collection = _get_collection()

    try:
        document = collection.find_one({"_id": recipe_id})
    except PyMongoError as e:
        raise StorageUnavailable(f"Couldn't read the recipe: {e}")

    if document is None:
        return None

    return {
        "id": document["_id"],
        "order": document.get("order", ""),
        "drink_name": document.get("drink_name", ""),
        "prep_time": document.get("prep_time"),
        "recipe": document.get("recipe", ""),
    }
