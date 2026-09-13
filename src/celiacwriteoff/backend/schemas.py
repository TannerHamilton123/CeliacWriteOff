from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Source = Literal["file", "manual"]
Status = Literal["pending", "extracted", "failed", "verified"]


class LineItem(BaseModel):
    item_name: str | None = None
    item_quantity: float | None = None
    item_price: float | None = None
    is_gluten_substitute: bool = False
    matched_product_name: str | None = None
    allergens_tags: list[str] = []
    contains_gluten: bool | None = None
    labeled_gluten_free: bool | None = None


class ItemCreate(BaseModel):
    name: str = ""
    notes: str = ""
    merchant_name: str | None = None
    merchant_address: str | None = None
    transaction_date: str | None = None
    transaction_time: str | None = None
    total_amount: float | None = None
    line_items: list[LineItem] = []


class ItemDraft(BaseModel):
    draft_id: str
    original_filename: str
    status: Literal["extracted", "failed"]
    merchant_name: str | None = None
    merchant_address: str | None = None
    transaction_date: str | None = None
    transaction_time: str | None = None
    total_amount: float | None = None
    line_items: list[LineItem] = []
    error_message: str | None = None


class ItemConfirm(BaseModel):
    draft_id: str
    original_filename: str
    name: str = ""
    notes: str = ""
    merchant_name: str | None = None
    merchant_address: str | None = None
    transaction_date: str | None = None
    transaction_time: str | None = None
    total_amount: float | None = None
    line_items: list[LineItem] = []


class ItemUpdate(BaseModel):
    name: str | None = None
    notes: str | None = None
    merchant_name: str | None = None
    merchant_address: str | None = None
    transaction_date: str | None = None
    transaction_time: str | None = None
    total_amount: float | None = None
    line_items: list[LineItem] | None = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    created_at: str


class ItemOut(BaseModel):
    id: str
    source: Source
    status: Status
    name: str
    notes: str
    original_filename: str | None = None
    merchant_name: str | None = None
    merchant_address: str | None = None
    transaction_date: str | None = None
    transaction_time: str | None = None
    total_amount: float | None = None
    line_items: list[LineItem] = []
    error_message: str | None = None
    created_at: str
    updated_at: str
    verified_at: str | None = None
