from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import Optional
from ..database import get_session
from ..models import ContractingAuthority

router = APIRouter(prefix="/authorities", tags=["Contracting Authorities"])


@router.get("/")
def get_authorities(
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100),
        name: Optional[str] = Query(None, description="Filter by name"),
        city: Optional[str] = Query(None, description="Filter by city"),
        session: Session = Depends(get_session)
):
    """Get paginated list of contracting authorities"""
    statement = select(ContractingAuthority)

    if name:
        statement = statement.where(ContractingAuthority.name.ilike(f"%{name}%"))
    if city:
        statement = statement.where(ContractingAuthority.city == city)

    total = len(session.exec(statement).all())
    offset = (page - 1) * page_size

    authorities = session.exec(statement.offset(offset).limit(page_size)).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": authorities
    }


@router.get("/{authority_id}")
def get_authority(authority_id: int, session: Session = Depends(get_session)):
    """Get a single contracting authority by ID"""
    authority = session.get(ContractingAuthority, authority_id)
    if not authority:
        raise HTTPException(status_code=404, detail=f"Authority with id {authority_id} not found")
    return authority
