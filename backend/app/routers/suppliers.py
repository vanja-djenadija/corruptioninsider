from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import Optional
from ..database import get_session
from ..models import Supplier

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("/")
def get_suppliers(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Items per page"),
        name: Optional[str] = Query(None, description="Filter by name (partial match)"),
        tax_number: Optional[str] = Query(None, description="Filter by tax number"),
        country: Optional[str] = Query(None, description="Filter by country"),
        is_foreign: Optional[bool] = Query(None, description="Filter by foreign status"),
        session: Session = Depends(get_session)
):
    """Get paginated list of suppliers with optional filters"""
    # Build query
    statement = select(Supplier)

    if name:
        statement = statement.where(Supplier.name.ilike(f"%{name}%"))
    if tax_number:
        statement = statement.where(Supplier.tax_number == tax_number)
    if country:
        statement = statement.where(Supplier.country == country)
    if is_foreign is not None:
        statement = statement.where(Supplier.is_foreign == is_foreign)

    # Get total count
    count_statement = select(Supplier).where(*statement.whereclause.clauses if statement.whereclause else [])
    total = len(session.exec(count_statement).all())

    # Apply pagination
    offset = (page - 1) * page_size
    statement = statement.offset(offset).limit(page_size)

    suppliers = session.exec(statement).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": suppliers
    }


@router.get("/{supplier_id}")
def get_supplier(supplier_id: int, session: Session = Depends(get_session)):
    """Get a single supplier by ID"""
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier with id {supplier_id} not found")
    return supplier


@router.get("/tax/{tax_number}")
def get_supplier_by_tax_number(tax_number: str, session: Session = Depends(get_session)):
    """Get suppliers by tax number"""
    statement = select(Supplier).where(Supplier.tax_number == tax_number)
    suppliers = session.exec(statement).all()
    if not suppliers:
        raise HTTPException(status_code=404, detail=f"No suppliers found with tax number {tax_number}")
    return suppliers
