from sqlmodel import SQLModel, Field
from typing import Optional


class CompanyRelation(SQLModel, table=True):
    __tablename__ = "company_relation"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_record_id: int = Field(foreign_key="company.id")
    data_hash: Optional[str] = Field(default=None, max_length=255)
    relation_type_id: Optional[int] = Field(default=None)
    full_name: Optional[str] = Field(default=None, max_length=500)
    share: Optional[int] = Field(default=None)
    position: Optional[str] = Field(default=None, max_length=255)