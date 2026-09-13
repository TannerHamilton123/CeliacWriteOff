import mimetypes
import sqlite3
from pathlib import Path
from typing import Annotated, Any

import allergens
import db
import kroger_client
import storage
from auth import CurrentUserDep
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from openai import OpenAIError
from PIL import UnidentifiedImageError
from receipt_extraction import extract_receipt_data
from schemas import ItemConfirm, ItemCreate, ItemDraft, ItemOut, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

DBDep = Annotated[sqlite3.Connection, Depends(db.get_db)]


def _get_item_or_404(conn: sqlite3.Connection, item_id: str, user_id: str) -> dict:
    item = db.get_item(conn, item_id, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


def _validated_extension(filename: str | None) -> str:
    extension = Path(filename or "").suffix.lower()
    if extension not in storage.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Allowed: {sorted(storage.ALLOWED_EXTENSIONS)}",
        )
    return extension


def _find_draft_file_or_404(draft_id: str) -> Path:
    file_path = storage.find_upload_file(draft_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Draft upload not found")
    return file_path


def _with_allergen_lookup(line_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Best-effort enrichment; a failed or missing match just leaves fields unset.

    Tries Kroger's catalog first (more accurate match against receipt text,
    curated allergen declarations) and falls back to Open Food Facts.
    """
    for line_item in line_items:
        name = line_item.get("item_name") or ""
        match = kroger_client.lookup_allergens(name) or allergens.lookup_allergens(name)
        if match is not None:
            line_item.update(match)
    return line_items


@router.get("/")
def list_items(conn: DBDep, current_user: CurrentUserDep) -> list[ItemOut]:
    return db.list_items(conn, current_user["id"])


@router.post("/")
def create_item(item: ItemCreate, conn: DBDep, current_user: CurrentUserDep) -> ItemOut:
    item_id = db.create_manual_item(
        conn,
        current_user["id"],
        item.name,
        item.notes,
        item.merchant_name,
        item.merchant_address,
        item.transaction_date,
        item.transaction_time,
        item.total_amount,
        [li.model_dump() for li in item.line_items],
    )
    return db.get_item(conn, item_id, current_user["id"])


@router.post("/upload")
def upload_item(file: UploadFile, current_user: CurrentUserDep) -> ItemDraft:
    """Save the file and run OCR, but do not persist anything to the database yet.

    The result is a draft the user reviews/edits on the frontend; a row is only
    created once they confirm it via POST /items/confirm.
    """
    extension = _validated_extension(file.filename)
    draft_id = db.new_item_id()
    dest_path = storage.upload_path(draft_id, extension)
    storage.ensure_storage_dirs()
    dest_path.write_bytes(file.file.read())
    original_filename = file.filename or ""

    try:
        extraction = extract_receipt_data(str(dest_path))
    except (FileNotFoundError, UnidentifiedImageError) as exc:
        return ItemDraft(
            draft_id=draft_id,
            original_filename=original_filename,
            status="failed",
            error_message=f"Unreadable image: {exc}",
        )
    except OpenAIError as exc:
        return ItemDraft(
            draft_id=draft_id,
            original_filename=original_filename,
            status="failed",
            error_message=f"OpenAI API error: {exc}",
        )

    if "error" in extraction:
        return ItemDraft(
            draft_id=draft_id,
            original_filename=original_filename,
            status="failed",
            error_message=str(extraction["error"]),
        )

    return ItemDraft(
        draft_id=draft_id,
        original_filename=original_filename,
        status="extracted",
        merchant_name=extraction.get("merchant_name"),
        merchant_address=extraction.get("merchant_address"),
        transaction_date=extraction.get("transaction_date"),
        transaction_time=extraction.get("transaction_time"),
        total_amount=db.coerce_float(extraction.get("total_amount")),
        line_items=_with_allergen_lookup(extraction.get("line_items") or []),
    )


@router.get("/draft/{draft_id}/file")
def get_draft_file(draft_id: str, current_user: CurrentUserDep) -> FileResponse:
    file_path = _find_draft_file_or_404(draft_id)
    return FileResponse(file_path, media_type=mimetypes.guess_type(file_path.name)[0])


@router.post("/confirm")
def confirm_item(payload: ItemConfirm, conn: DBDep, current_user: CurrentUserDep) -> ItemOut:
    """Create the DB row for a previously-uploaded draft, using the user's reviewed fields."""
    file_path = _find_draft_file_or_404(payload.draft_id)
    mime_type = mimetypes.guess_type(file_path.name)[0] or ""
    db.create_confirmed_file_item(
        conn,
        payload.draft_id,
        current_user["id"],
        str(file_path),
        payload.original_filename,
        mime_type,
        payload.name,
        payload.notes,
        payload.merchant_name,
        payload.merchant_address,
        payload.transaction_date,
        payload.transaction_time,
        payload.total_amount,
        [li.model_dump() for li in payload.line_items],
    )
    return db.get_item(conn, payload.draft_id, current_user["id"])


@router.delete("/draft/{draft_id}", status_code=204)
def discard_draft(draft_id: str, current_user: CurrentUserDep) -> None:
    file_path = _find_draft_file_or_404(draft_id)
    file_path.unlink(missing_ok=True)


@router.get("/{item_id}/file")
def get_item_file(item_id: str, conn: DBDep, current_user: CurrentUserDep) -> FileResponse:
    row = db.get_item_row(conn, item_id, current_user["id"])
    if row is None or not row["file_path"]:
        raise HTTPException(status_code=404, detail="No file for this item")
    file_path = Path(row["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(file_path, media_type=row["mime_type"] or None)


@router.patch("/{item_id}")
def update_item(
    item_id: str, updates: ItemUpdate, conn: DBDep, current_user: CurrentUserDep
) -> ItemOut:
    _get_item_or_404(conn, item_id, current_user["id"])
    changes = updates.model_dump(exclude_unset=True)
    db.update_item(conn, item_id, current_user["id"], changes)
    return db.get_item(conn, item_id, current_user["id"])


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: str, conn: DBDep, current_user: CurrentUserDep) -> None:
    row = db.get_item_row(conn, item_id, current_user["id"])
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    storage.delete_file(row["file_path"])
    db.delete_item(conn, item_id, current_user["id"])
