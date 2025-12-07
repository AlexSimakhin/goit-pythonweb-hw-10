"""
FastAPI router for managing contact endpoints.
Implements RESTful routes for CRUD operations, search, and upcoming birthdays.
"""
from typing import List
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.contact import ContactCreate, ContactUpdate, ContactOut
from app.crud.contact import create_contact, get_contacts, get_contact, update_contact, delete_contact, search_contacts, get_upcoming_birthdays

router = APIRouter(prefix="/contacts", tags=["contacts"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_db():
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ContactOut)
async def create_contact_route(contact: ContactCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Create a new contact."""
    return create_contact(db, contact, token)

@router.get("/", response_model=List[ContactOut])
async def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Get list of contacts."""
    return get_contacts(db, skip, limit, token)

@router.get("/{contact_id}", response_model=ContactOut)
async def read_contact(contact_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Get contact by ID."""
    return get_contact(db, contact_id, token)

@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact_route(contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Update contact by ID."""
    return update_contact(db, contact_id, contact, token)

@router.delete("/{contact_id}", response_model=bool)
async def delete_contact_route(contact_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Delete contact by ID."""
    return delete_contact(db, contact_id, token)

@router.get("/search", response_model=List[ContactOut])
async def search_contacts_route(query: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Search contacts by name or email."""
    return search_contacts(db, query, token)

@router.get("/birthdays/upcoming", response_model=List[ContactOut])
async def upcoming_birthdays_route(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Get contacts with upcoming birthdays."""
    return get_upcoming_birthdays(db, token)
