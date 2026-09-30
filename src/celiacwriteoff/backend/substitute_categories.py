"""Common products that celiacs have to buy a gluten-free version of.

Each category maps to the Kroger search term for the *regular* (gluten-containing)
equivalent. The IRS medical-expense deduction for gluten-free food is only the
extra cost over the regular product, so the regular product's price is the
number we compare the receipt price against.
"""

from typing import TypedDict


class SubstituteCategory(TypedDict):
    label: str
    search_term: str


SUBSTITUTE_CATEGORIES: dict[str, SubstituteCategory] = {
    "bread": {"label": "Sandwich bread", "search_term": "white sandwich bread"},
    "buns": {"label": "Hamburger / hot dog buns", "search_term": "hamburger buns"},
    "bagels": {"label": "Bagels", "search_term": "plain bagels"},
    "english_muffins": {"label": "English muffins", "search_term": "english muffins"},
    "tortillas": {"label": "Tortillas / wraps", "search_term": "flour tortillas"},
    "pasta": {"label": "Pasta", "search_term": "spaghetti pasta"},
    "mac_and_cheese": {"label": "Boxed mac & cheese", "search_term": "macaroni and cheese dinner"},
    "crackers": {"label": "Crackers", "search_term": "saltine crackers"},
    "pretzels": {"label": "Pretzels", "search_term": "pretzel twists"},
    "cereal": {"label": "Cereal", "search_term": "corn flakes cereal"},
    "oats": {"label": "Oats / oatmeal", "search_term": "old fashioned oats"},
    "flour": {"label": "Flour", "search_term": "all purpose flour"},
    "baking_mix": {"label": "Pancake / baking mix", "search_term": "pancake mix"},
    "cake_mix": {"label": "Cake / brownie mix", "search_term": "cake mix"},
    "cookies": {"label": "Cookies", "search_term": "sandwich cookies"},
    "breadcrumbs": {"label": "Breadcrumbs", "search_term": "plain bread crumbs"},
    "pizza": {"label": "Frozen pizza", "search_term": "frozen cheese pizza"},
    "pizza_crust": {"label": "Pizza crust", "search_term": "pizza crust"},
    "waffles": {"label": "Frozen waffles", "search_term": "frozen waffles"},
    "chicken_nuggets": {"label": "Breaded chicken nuggets", "search_term": "frozen chicken nuggets"},
    "soy_sauce": {"label": "Soy sauce", "search_term": "soy sauce"},
    "granola_bars": {"label": "Granola / snack bars", "search_term": "chewy granola bars"},
    "beer": {"label": "Beer", "search_term": "beer 6 pack"},
}
