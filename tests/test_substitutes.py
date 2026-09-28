"""Tests for gluten-free substitute categories and the Kroger cheapest-price lookup."""

import kroger_client
import pytest
from substitute_categories import SUBSTITUTE_CATEGORIES


@pytest.fixture
def logged_in_client(client):
    response = client.post(
        "/auth/signup",
        json={
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "Str0ng!Passw0rd",
            "confirm_password": "Str0ng!Passw0rd",
            "recaptcha_token": "",
        },
    )
    assert response.status_code == 201
    return client


def test_cheapest_product_prefers_lowest_price_across_variants():
    products = [
        {
            "description": "Brand A Bread",
            "items": [{"size": "20 oz", "price": {"regular": 3.49, "promo": 0}}],
        },
        {
            "description": "Brand B Bread",
            "items": [
                {"size": "24 oz", "price": {"regular": 2.99, "promo": 0}},
                {"size": "16 oz", "price": {"regular": 2.49, "promo": 1.99}},
            ],
        },
        # No price at this store -- skipped rather than treated as free.
        {"description": "Brand C Bread", "items": [{"size": "20 oz"}]},
    ]

    assert kroger_client.cheapest_product(products) == {
        "product_name": "Brand B Bread",
        "size": "16 oz",
        "price": 1.99,
    }


def test_cheapest_product_with_no_prices_returns_none():
    assert kroger_client.cheapest_product([{"description": "x", "items": [{}]}]) is None


def test_find_cheapest_product_needs_location(monkeypatch):
    monkeypatch.delenv("KROGER_LOCATION_ID", raising=False)
    monkeypatch.setattr(kroger_client, "load_dotenv", lambda: None)
    assert kroger_client.find_cheapest_product("white bread") is None


def test_list_categories_requires_login(client):
    assert client.get("/substitutes/categories").status_code == 401


def test_list_categories(logged_in_client):
    response = logged_in_client.get("/substitutes/categories")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(SUBSTITUTE_CATEGORIES)
    assert {"key": "bread", "label": "Sandwich bread"} in body


def test_cheapest_in_category(logged_in_client, monkeypatch):
    searched_terms = []

    def fake_find(search_term):
        searched_terms.append(search_term)
        return {"product_name": "Kroger White Bread", "size": "20 oz", "price": 1.29}

    monkeypatch.setattr(kroger_client, "find_cheapest_product", fake_find)

    response = logged_in_client.get("/substitutes/categories/bread/cheapest")

    assert response.status_code == 200
    assert response.json() == {
        "category": "bread",
        "product_name": "Kroger White Bread",
        "size": "20 oz",
        "price": 1.29,
    }
    assert searched_terms == [SUBSTITUTE_CATEGORIES["bread"]["search_term"]]


def test_cheapest_in_category_unavailable(logged_in_client, monkeypatch):
    monkeypatch.setattr(kroger_client, "find_cheapest_product", lambda term: None)

    response = logged_in_client.get("/substitutes/categories/bread/cheapest")

    assert response.status_code == 200
    assert response.json()["price"] is None


def test_cheapest_in_unknown_category(logged_in_client):
    response = logged_in_client.get("/substitutes/categories/not-a-thing/cheapest")
    assert response.status_code == 404
