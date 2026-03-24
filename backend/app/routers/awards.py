from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import Optional
from datetime import date
from decimal import Decimal
from ..database import get_session
from ..models import Award

router = APIRouter(prefix="/awards", tags=["Awards"])


@router.get("/")
def get_awards(
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100),
        contracting_authority_id: Optional[int] = Query(None),
        procedure_id: Optional[int] = Query(None),
        min_value: Optional[Decimal] = Query(None, description="Minimum contract value"),
        max_value: Optional[Decimal] = Query(None, description="Maximum contract value"),
        session: Session = Depends(get_session)
):
    """Get paginated list of awards with filters"""
    statement = select(Award)

    if contracting_authority_id:
        statement = statement.where(Award.contracting_authority_id == contracting_authority_id)
    if procedure_id:
        statement = statement.where(Award.procedure_id == procedure_id)
    if min_value:
        statement = statement.where(Award.value >= min_value)
    if max_value:
        statement = statement.where(Award.value <= max_value)

    total = len(session.exec(statement).all())
    offset = (page - 1) * page_size

    awards = session.exec(statement.offset(offset).limit(page_size)).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": awards
    }


@router.get("/{award_id}")
def get_award(award_id: int, session: Session = Depends(get_session)):
    """Get a single award by ID"""
    award = session.get(Award, award_id)
    if not award:
        raise HTTPException(status_code=404, detail=f"Award with id {award_id} not found")
    return award
