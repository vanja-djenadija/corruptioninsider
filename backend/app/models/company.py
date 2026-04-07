from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from typing import Optional
from datetime import datetime


class Company(SQLModel, table=True):
    __tablename__ = "company"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: Optional[str] = Field(default=None, max_length=50)
    data_hash: Optional[str] = Field(default=None, max_length=255)
    company_short_name: Optional[str] = Field(default=None, max_length=500)
    company_long_name: Optional[str] = Field(default=None, max_length=500)
    municipality: Optional[str] = Field(default=None, max_length=255)
    county: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    letter_of_activity: Optional[str] = Field(default=None, max_length=100)
    activity_code: Optional[str] = Field(default=None, max_length=100)
    activity_code_description: Optional[str] = Field(default=None, max_length=500)
    registration_date: Optional[datetime] = Field(default=None)
    is_public_entity: Optional[bool] = Field(default=None)
    imported_at: Optional[datetime] = Field(default=None)