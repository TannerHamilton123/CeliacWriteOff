"""Look up allergen tags for receipt line items via the Open Food Facts search API."""

from functools import lru_cache
from typing import Any

import httpx

SEARCH_URL = "https://search.openfoodfacts.org/search"
USER_AGENT = "CeliacWriteOff/0.1 (tannerhamilton2000@gmail.com)"
GLUTEN_TAG = "en:gluten"


@lru_cache(maxsize=512)
def lookup_allergens(item_name: str) -> dict[str, Any] | None:
    """Best-effort match of a receipt item name to an Open Food Facts product.

    Returns None if the lookup fails or no product matches. Matching is by
    fuzzy text search on the name OCR'd from a receipt, so results are a
    suggestion for the user to confirm, not an authoritative answer.
    """
    name = item_name.strip()
    if not name:
        return None

    try:
        response = httpx.get(
            SEARCH_URL,
            params={
                "q": name,
                "fields": "product_name,allergens_tags,labels_tags",
                "page_size": 1,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=5.0,
        )
        response.raise_for_status()
        hits = response.json().get("hits") or []
    except (httpx.HTTPError, ValueError):
        return None

    if not hits:
        return None

    hit = hits[0]
    allergens_tags = hit.get("allergens_tags") or []
    labels_tags = hit.get("labels_tags") or []
    return {
        "matched_product_name": hit.get("product_name"),
        "allergens_tags": allergens_tags,
        "contains_gluten": GLUTEN_TAG in allergens_tags,
        "labeled_gluten_free": "en:gluten-free" in labels_tags,
    }
