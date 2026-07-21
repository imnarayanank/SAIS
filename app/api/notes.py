"""
app/api/notes.py
-----------------
Notes CRUD routes + attachment upload/delete.

Endpoints:
  GET    /api/notes/              – list all notes for the current user
  POST   /api/notes/              – create a new note
  GET    /api/notes/{id}          – get a single note
  PUT    /api/notes/{id}          – update a note (full/partial)
  PATCH  /api/notes/{id}/favourite – toggle is_favourite
  DELETE /api/notes/{id}          – delete a note

  POST   /api/notes/{id}/attachments          – upload a file attachment
  DELETE /api/notes/{id}/attachments/{fname}  – remove an attachment
"""
import os
import uuid
import json
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..core.config import settings
from ..core.deps import get_current_user
from ..models.user import User
from ..models.note import Note
from ..schemas.note import NoteCreate, NoteUpdate, NoteOut

router = APIRouter(prefix="/api/notes", tags=["Notes"])

# ── Allowed MIME types / extensions for attachments ──────────────
ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp", "svg",
    "mp4", "mov", "webm", "avi", "mkv",
    "mp3", "wav", "m4a", "ogg",
    "pdf",
    "doc", "docx",
}


def _get_note_or_404(note_id: int, user: User, db: Session) -> Note:
    note = db.query(Note).filter(
        Note.note_id == note_id,
        Note.user_id == user.user_id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


def _parse_attachments(raw: str | None) -> list:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _dump_attachments(attachments: list) -> str:
    return json.dumps(attachments)


# ── List ─────────────────────────────────────────────────────────
@router.get("/", response_model=List[NoteOut])
def list_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all notes belonging to the current user, newest first."""
    notes = (
        db.query(Note)
        .filter(Note.user_id == current_user.user_id)
        .order_by(Note.updated_at.desc())
        .all()
    )
    return notes


# ── Create ───────────────────────────────────────────────────────
@router.post("/", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new note."""
    note = Note(**data.model_dump(), user_id=current_user.user_id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ── Get one ──────────────────────────────────────────────────────
@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch a single note by ID."""
    return _get_note_or_404(note_id, current_user, db)


# ── Update ───────────────────────────────────────────────────────
@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a note (supports partial updates)."""
    note = _get_note_or_404(note_id, current_user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


# ── Toggle favourite ─────────────────────────────────────────────
@router.patch("/{note_id}/favourite", response_model=NoteOut)
def toggle_favourite(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle the is_favourite flag on a note."""
    note = _get_note_or_404(note_id, current_user, db)
    note.is_favourite = not note.is_favourite
    db.commit()
    db.refresh(note)
    return note


# ── Delete ───────────────────────────────────────────────────────
@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a note and its attachment files from disk."""
    note = _get_note_or_404(note_id, current_user, db)

    # Remove any uploaded attachment files
    attachments = _parse_attachments(note.attachments)
    for att in attachments:
        file_path = os.path.join(settings.UPLOAD_DIR, att.get("path", ""))
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    db.delete(note)
    db.commit()


# ── Upload attachment ─────────────────────────────────────────────
@router.post("/{note_id}/attachments", response_model=NoteOut)
def upload_attachment(
    note_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a file attachment and append it to the note."""
    note = _get_note_or_404(note_id, current_user, db)

    # Validate extension
    original_filename = file.filename or "upload"
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Validate size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)     # Reset
    if size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    # Save to uploads/<note_attachments>/<unique>_<original>
    note_dir = os.path.join(settings.UPLOAD_DIR, "notes", str(note_id))
    os.makedirs(note_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{original_filename}"
    save_path = os.path.join(note_dir, unique_name)
    with open(save_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    # Relative path used for URL construction on the frontend
    relative_path = os.path.join("notes", str(note_id), unique_name).replace("\\", "/")

    attachments = _parse_attachments(note.attachments)
    attachments.append({
        "filename": original_filename,
        "path": relative_path,
        "size": size,
    })
    note.attachments = _dump_attachments(attachments)
    db.commit()
    db.refresh(note)
    return note


# ── Delete attachment ─────────────────────────────────────────────
@router.delete("/{note_id}/attachments/{filename}", response_model=NoteOut)
def delete_attachment(
    note_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a single attachment from a note."""
    note = _get_note_or_404(note_id, current_user, db)

    attachments = _parse_attachments(note.attachments)
    to_remove = next(
        (a for a in attachments if a.get("path", "").endswith(filename)),
        None,
    )
    if not to_remove:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Delete physical file
    file_path = os.path.join(settings.UPLOAD_DIR, to_remove["path"])
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    attachments = [a for a in attachments if a.get("path") != to_remove["path"]]
    note.attachments = _dump_attachments(attachments)
    db.commit()
    db.refresh(note)
    return note
