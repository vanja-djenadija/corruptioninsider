from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import Optional
from ..database import get_session
from ..models import ProcurementProcedure

router = APIRouter(prefix="/procedures", tags=["Procurement Procedures"])


@router.get("/")
def get_procedures(
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100),
        type: Optional[str] = Query(None, description="Filter by procedure type"),
        contract_type: Optional[str] = Query(None, description="Filter by contract type"),
        session: Session = Depends(get_session)
):
    """Get paginated list of procurement procedures"""
    statement = select(ProcurementProcedure)

    if type:
        statement = statement.where(ProcurementProcedure.type == type)
    if contract_type:
        statement = statement.where(ProcurementProcedure.contract_type == contract_type)

    total = len(session.exec(statement).all())
    offset = (page - 1) * page_size

    procedures = session.exec(statement.offset(offset).limit(page_size)).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": procedures
    }


@router.get("/{procedure_id}")
def get_procedure(procedure_id: int, session: Session = Depends(get_session)):
    """Get a single procedure by ID"""
    procedure = session.get(ProcurementProcedure, procedure_id)
    if not procedure:
        raise HTTPException(status_code=404, detail=f"Procedure with id {procedure_id} not found")
    return procedure


@router.get("/number/{procedure_number}")
def get_procedure_by_number(procedure_number: str, session: Session = Depends(get_session)):
    """Get a procedure by its unique number"""
    statement = select(ProcurementProcedure).where(ProcurementProcedure.number == procedure_number)
    procedure = session.exec(statement).first()
    if not procedure:
        raise HTTPException(status_code=404, detail=f"Procedure with number {procedure_number} not found")
    return procedure
