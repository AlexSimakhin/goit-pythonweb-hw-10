"""
CRUD operations for managing contacts in the database.
Implements create, read, update, delete, search, and upcoming birthdays logic.
"""

from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate
from app.utils.auth import decode_access_token


def create_contact(db: Session, contact: ContactCreate, token: str) -> Contact:
    """
    Create a new contact.

    Args:
        db (Session): The database session.
        contact (ContactCreate): The contact data to create.
        token (str): The access token of the user.

    Returns:
        Contact: The created contact.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("user_id")
    contact_data = contact.model_dump()
    contact_data.pop("user_id", None)
    db_contact = Contact(**contact_data, user_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def get_contacts(db: Session, skip: int = 0, limit: int = 100, token: str = None) -> List[Contact]:
    """
    Get a list of contacts.

    Args:
        db (Session): The database session.
        skip (int): Number of contacts to skip (for pagination).
        limit (int): Maximum number of contacts to return.
        token (str, optional): The access token of the user.

    Returns:
        List[Contact]: A list of contacts.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("user_id")
    return db.query(Contact).filter(Contact.user_id == user_id).offset(skip).limit(limit).all()


def get_contact(db: Session, contact_id: int, token: str = None) -> Optional[Contact]:
    """
    Get a contact by ID.

    Args:
        db (Session): The database session.
        contact_id (int): The ID of the contact to retrieve.
        token (str, optional): The access token of the user.

    Returns:
        Optional[Contact]: The contact if found, otherwise None.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("user_id")
    return db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()


def update_contact(db: Session, contact_id: int, contact: ContactUpdate, token: str = None) -> Optional[Contact]:
    """
    Update an existing contact.

    Args:
        db (Session): The database session.
        contact_id (int): The ID of the contact to update.
        contact (ContactUpdate): The new contact data.
        token (str, optional): The access token of the user.

    Returns:
        Optional[Contact]: The updated contact if found and updated, otherwise None.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("user_id")
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if db_contact:
        for key, value in contact.model_dump(exclude_unset=True).items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, contact_id: int, token: str = None) -> bool:
    """
    Delete a contact.

    Args:
        db (Session): The database session.
        contact_id (int): The ID of the contact to delete.
        token (str, optional): The access token of the user.

    Returns:
        bool: True if the contact was deleted, otherwise False.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("user_id")
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
        return True
    return False


def search_contacts(db: Session, query: str, token: str = None) -> List[Contact]:
    """
    Search contacts by first name, last name, or email.

    Args:
        db (Session): The database session.
        query (str): The search query.
        token (str, optional): The access token of the user.

    Returns:
        List[Contact]: A list of contacts matching the search query.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("user_id")
    return db.query(Contact).filter(
        Contact.user_id == user_id,
        or_(
            Contact.first_name.ilike(f"%{query}%"),
            Contact.last_name.ilike(f"%{query}%"),
            Contact.email.ilike(f"%{query}%"),
        )
    ).all()


def get_upcoming_birthdays(db: Session, token: str = None) -> List[Contact]:
    """
    Get contacts with upcoming birthdays in the next 7 days.

    Args:
        db (Session): The database session.
        token (str, optional): The access token of the user.

    Returns:
        List[Contact]: A list of contacts with upcoming birthdays.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("user_id")
    today = date.today()
    next_week = today + timedelta(days=7)
    contacts = db.query(Contact).filter(Contact.user_id == user_id).all()
    upcoming: List[Contact] = []
    for c in contacts:
        # Normalize birthday to current year
        bday_this_year = c.birthday.replace(year=today.year)
        # Handle new year wrap: if already passed, check next year
        if bday_this_year < today:
            bday_this_year = c.birthday.replace(year=today.year + 1)
        if today <= bday_this_year <= next_week:
            upcoming.append(c)
    return upcoming
