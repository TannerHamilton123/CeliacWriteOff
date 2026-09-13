"""OAuth2 client-credentials access to Kroger's Product API, for allergen lookups."""

import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv

TOKEN_URL = "https://api.kroger.com/v1/connect/oauth2/token"
PRODUCTS_URL = "https://api.kroger.com/v1/products"
GLUTEN_KEYWORDS = ("gluten", "cereal", "wheat")

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


def _get_access_token() -> str | None:
    load_dotenv()
    client_id = os.getenv("KROGER_CLIENT_ID")
    client_secret = os.getenv("KROGER_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    if _token_cache["access_token"] and time.monotonic() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    try:
        response = httpx.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials", "scope": "product.compact"},
            auth=(client_id, client_secret),
            timeout=5.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    access_token = payload.get("access_token")
    if not access_token:
        return None

    # Refresh a little early so a request doesn't land right on expiry.
    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = time.monotonic() + payload.get("expires_in", 1800) - 60
    return access_token


def _contains_gluten(allergens: list[dict[str, Any]]) -> bool | None:
    for allergen in allergens:
        name = (allergen.get("name") or "").lower()
        if any(keyword in name for keyword in GLUTEN_KEYWORDS):
            level = (allergen.get("levelOfContainmentName") or "").lower()
            return "free" not in level
    return None


def lookup_allergens(item_name: str) -> dict[str, Any] | None:
    """Best-effort match of a receipt item name to a Kroger catalog product.

    Returns None if credentials aren't configured, the request fails, or
    nothing matches. Matching is by fuzzy text search on the name OCR'd from
    a receipt, so results are a suggestion for the user to confirm.
    """
    name = item_name.strip()
    if not name:
        return None

    access_token = _get_access_token()
    if access_token is None:
        return None

    try:
        response = httpx.get(
            PRODUCTS_URL,
            params={"filter.term": name, "filter.limit": 1},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json().get("data")
    except (httpx.HTTPError, ValueError):
        return None

    if isinstance(data, list):
        product = data[0] if data else None
    else:
        product = data
    if not product:
        return None

    allergens = product.get("allergens") or []
    return {
        "matched_product_name": product.get("receiptDescription") or product.get("description"),
        "allergens_tags": [
            f"{a.get('levelOfContainmentName', '')}: {a.get('name', '')}".strip(": ")
            for a in allergens
        ],
        "contains_gluten": _contains_gluten(allergens),
        "labeled_gluten_free": None,
    }
