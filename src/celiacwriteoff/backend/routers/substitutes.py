import kroger_client
from auth import CurrentUserDep
from fastapi import APIRouter, HTTPException
from schemas import CategoryPriceOut, SubstituteCategoryOut
from substitute_categories import SUBSTITUTE_CATEGORIES

router = APIRouter(prefix="/substitutes", tags=["substitutes"])


@router.get("/categories")
def list_categories(current_user: CurrentUserDep) -> list[SubstituteCategoryOut]:
    return [
        SubstituteCategoryOut(key=key, label=category["label"])
        for key, category in SUBSTITUTE_CATEGORIES.items()
    ]


@router.get("/categories/{category}/cheapest")
def cheapest_in_category(category: str, current_user: CurrentUserDep) -> CategoryPriceOut:
    """Cheapest regular (non-gluten-free) product in this category at the configured Kroger store.

    Responds with price=None rather than an error when Kroger isn't
    configured or has no priced match, so the UI can just show "unavailable".
    """
    if category not in SUBSTITUTE_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Unknown category '{category}'")

    match = kroger_client.find_cheapest_product(SUBSTITUTE_CATEGORIES[category]["search_term"])
    return CategoryPriceOut(category=category, **(match or {}))
