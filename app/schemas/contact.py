"""
Pydantic schemas for validating and serializing contact data.
Defines base, create, update, and output schemas for contacts.
"""
from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field

class ContactBase(BaseModel):
    """Base schema for contact information."""
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    email: EmailStr
    phone: str
    birthday: date
    extra: Optional[str] = None
    user_id: Optional[int] = None

class ContactCreate(ContactBase):
    """Schema for creating a new contact."""
    # No additional fields; inherits all from ContactBase

class ContactUpdate(ContactBase):
    """Schema for updating a contact."""
    # No additional fields; inherits all from ContactBase

class ContactOut(ContactBase):
    """Schema for outputting contact information."""
    id: int

    class Config:
        """Pydantic config for ORM mode."""
        from_attributes = True
