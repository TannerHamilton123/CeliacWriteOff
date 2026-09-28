"""OAuth2 client-credentials access to Kroger's Product API, for allergen and price lookups."""

import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv

TOKEN_URL = "https://api.kroger.com/v1/connect/oauth2/token"
PRODUCTS_URL = "https://api.kroger.com/v1/products"
GLUTEN_KEYWORDS = ("gluten", "cereal", "wheat")
# Kroger caps filter.limit at 50.
MAX_SEARCH_RESULTS = 50

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


def _search_products(params: dict[str, Any]) -> list[dict[str, Any]] | None:
    """GET /products with the given query params; None if unconfigured or the request fails."""
    access_token = _get_access_token()
    if access_token is None:
        return None

    try:
        response = httpx.get(
            PRODUCTS_URL,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json().get("data")
    except (httpx.HTTPError, ValueError):
        return None

    if isinstance(data, list):
        return data
    return [data] if data else []


def lookup_allergens(item_name: str) -> dict[str, Any] | None:
    """Best-effort match of a receipt item name to a Kroger catalog product.

    Returns None if credentials aren't configured, the request fails, or
    nothing matches. Matching is by fuzzy text search on the name OCR'd from
    a receipt, so results are a suggestion for the user to confirm.
    """
    name = item_name.strip()
    if not name:
        return None

    products = _search_products({"filter.term": name, "filter.limit": 1})
    product = products[0] if products else None
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


def _effective_price(price: dict[str, Any] | None) -> float | None:
    """The price a shopper would pay: the promo price if there is one, else regular.

    Kroger reports promo as 0 when there's no sale on.
    """
    if not price:
        return None
    regular = price.get("regular") or 0
    promo = price.get("promo") or 0
    if promo > 0 and (regular <= 0 or promo < regular):
        return float(promo)
    if regular > 0:
        return float(regular)
    return None


def cheapest_product(products: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the lowest-priced item across a list of Kroger product results.

    Each product can have several `items` (package variants), each with its
    own price, so every variant is considered.
    """
    best: dict[str, Any] | None = None
    for product in products:
        for variant in product.get("items") or []:
            price = _effective_price(variant.get("price"))
            if price is None:
                continue
            if best is None or price < best["price"]:
                best = {
                    "product_name": product.get("description"),
                    "size": variant.get("size"),
                    "price": price,
                }
    return best


def find_cheapest_product(search_term: str) -> dict[str, Any] | None:
    """Cheapest product at the configured Kroger store matching `search_term`.

    Kroger only includes prices when the request names a store, so this needs
    KROGER_LOCATION_ID as well as the API credentials. Returns None if either
    is missing, the request fails, or no matching product has a price.
    """
    load_dotenv()
    location_id = os.getenv("KROGER_LOCATION_ID")
    if not location_id:
        return None

    products = _search_products(
        {
            "filter.term": search_term,
            "filter.locationId": location_id,
            "filter.limit": MAX_SEARCH_RESULTS,
        }
    )
    if not products:
        return None
    return cheapest_product(products)
