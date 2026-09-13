import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from receipt_ocr.processors import ReceiptProcessor
from receipt_ocr.providers import OpenAIProvider

JSON_SCHEMA = {
    "merchant_name": "string",
    "merchant_address": "string",
    "transaction_date": "string",
    "transaction_time": "string",
    "total_amount": "number",
    "line_items": [
        {
            "item_name": "string",
            "item_quantity": "number",
            "item_price": "number",
        }
    ],
}


@lru_cache
def _get_processor() -> ReceiptProcessor:
    load_dotenv()
    return ReceiptProcessor(OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY")))


def extract_receipt_data(image_path: str) -> dict[str, Any]:
    return _get_processor().process_receipt(image_path, JSON_SCHEMA, "gpt-4.1")
