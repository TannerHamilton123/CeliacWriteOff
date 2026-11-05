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


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("1234 Main St, Cincinnati, OH 45202", "45202"),
        # The street number is also 5 digits -- the ZIP is the last match.
        ("12345 Main St, Cincinnati, OH 45202", "45202"),
        ("100 Vine St Cincinnati OH 45202-1234", "45202"),
        ("Kroger Store #123", None),
        ("", None),
    ],
)
def test_extract_zip_code(address, expected):
    assert kroger_client.extract_zip_code(address) == expected


@pytest.fixture
def no_default_location(monkeypatch):
    monkeypatch.setattr(kroger_client, "load_dotenv", lambda: None)
    monkeypatch.delenv("KROGER_LOCATION_ID", raising=False)


def test_resolve_store_uses_nearest_store_to_receipt_zip(monkeypatch, no_default_location):
    looked_up = []

    def fake_nearest(zip_code):
        looked_up.append(zip_code)
        return {"location_id": "01400943", "name": "Kroger - Hyde Park"}

    monkeypatch.setattr(kroger_client, "find_nearest_store", fake_nearest)

    store = kroger_client.resolve_store("3760 Paxton Ave, Cincinnati, OH 45209")

    assert store == {"location_id": "01400943", "name": "Kroger - Hyde Park"}
    assert looked_up == ["45209"]


def test_resolve_store_falls_back_to_configured_location(monkeypatch, no_default_location):
    monkeypatch.setenv("KROGER_LOCATION_ID", "99999999")
    monkeypatch.setattr(kroger_client, "find_nearest_store", lambda zip_code: None)

    assert kroger_client.resolve_store("no zip here") == {"location_id": "99999999", "name": None}
    assert kroger_client.resolve_store(None) == {"location_id": "99999999", "name": None}


def test_resolve_store_with_nothing_configured(no_default_location):
    assert kroger_client.resolve_store(None) is None


def test_list_categories_requires_login(client):
    assert client.get("/substitutes/categories").status_code == 401


def test_list_categories(logged_in_client):
    response = logged_in_client.get("/substitutes/categories")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(SUBSTITUTE_CATEGORIES)
    assert {"key": "bread", "label": "Sandwich bread"} in body


def test_cheapest_in_category(logged_in_client, monkeypatch):
    addresses = []
    searches = []

    def fake_resolve(address):
        addresses.append(address)
        return {"location_id": "01400943", "name": "Kroger - Hyde Park"}

    def fake_find(search_term, location_id):
        searches.append((search_term, location_id))
        return {"product_name": "Kroger White Bread", "size": "20 oz", "price": 1.29}

    monkeypatch.setattr(kroger_client, "resolve_store", fake_resolve)
    monkeypatch.setattr(kroger_client, "find_cheapest_product", fake_find)

    response = logged_in_client.get(
        "/substitutes/categories/bread/cheapest",
        params={"address": "3760 Paxton Ave, Cincinnati, OH 45209"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "category": "bread",
        "product_name": "Kroger White Bread",
        "size": "20 oz",
        "price": 1.29,
        "store_name": "Kroger - Hyde Park",
    }
    assert addresses == ["3760 Paxton Ave, Cincinnati, OH 45209"]
    assert searches == [(SUBSTITUTE_CATEGORIES["bread"]["search_term"], "01400943")]


def test_cheapest_in_category_without_a_store(logged_in_client, monkeypatch):
    monkeypatch.setattr(kroger_client, "resolve_store", lambda address: None)

    response = logged_in_client.get("/substitutes/categories/bread/cheapest")

    assert response.status_code == 200
    assert response.json()["price"] is None


def test_cheapest_in_category_unavailable(logged_in_client, monkeypatch):
    monkeypatch.setattr(
        kroger_client, "resolve_store", lambda address: {"location_id": "1", "name": None}
    )
    monkeypatch.setattr(kroger_client, "find_cheapest_product", lambda term, location_id: None)

    response = logged_in_client.get("/substitutes/categories/bread/cheapest")

    assert response.status_code == 200
    assert response.json()["price"] is None


def test_cheapest_in_unknown_category(logged_in_client):
    response = logged_in_client.get("/substitutes/categories/not-a-thing/cheapest")
    assert response.status_code == 404
