from typing import Literal

from password_policy import validate_password_strength
from pydantic import BaseModel, EmailStr, Field, model_validator

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
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str
    confirm_password: str
    recaptcha_token: str

    @model_validator(mode="after")
    def check_password(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        validate_password_strength(self.password)
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    recaptcha_token: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    is_admin: bool
    created_at: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def check_password(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        validate_password_strength(self.new_password)
        return self


class LoginAttemptOut(BaseModel):
    id: str
    email: str
    user_id: str | None
    success: bool
    ip_address: str | None
    user_agent: str | None
    created_at: str


class LoginAttemptsPage(BaseModel):
    attempts: list[LoginAttemptOut]
    total: int


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
