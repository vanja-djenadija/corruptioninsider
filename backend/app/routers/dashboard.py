from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import List, Dict, Any
from ..database import get_session
from ..models import Award, Supplier, ProcurementProcedure, ContractingAuthority, CompanyRelation, Company
import json

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats/overview")
def get_overview_stats(session: Session = Depends(get_session)):
    """Get high-level overview statistics"""

    total_awards = session.query(func.count(Award.id)).scalar()
    total_value = session.query(func.sum(Award.value)).scalar() or 0
    total_suppliers = session.query(func.count(Supplier.id)).scalar()
    total_authorities = session.query(func.count(ContractingAuthority.id)).scalar()

    # Average bids per award
    avg_bids = session.query(func.avg(Award.number_of_received_offers)).scalar() or 0

    # Low competition rate (1 or fewer bids)
    low_competition = session.query(func.count(Award.id)).filter(
        Award.number_of_received_offers <= 1
    ).scalar()
    low_competition_rate = (low_competition / total_awards * 100) if total_awards > 0 else 0

    return {
        "total_awards": total_awards,
        "total_value": float(total_value),
        "total_suppliers": total_suppliers,
        "total_authorities": total_authorities,
        "avg_bids_per_award": round(float(avg_bids), 2),
        "low_competition_rate": round(low_competition_rate, 2)
    }


@router.get("/stats/procedure-types")
def get_procedure_types(session: Session = Depends(get_session)):
    """Get distribution of procedure types with risk levels"""

    # Define risk levels for different procedure types
    risk_mapping = {
        'Direct agreement': 'high',
        'Negotiated procedure': 'high',
        'Competitive procedure with negotiation': 'medium',
        'Open procedure': 'low',
        'Restricted procedure': 'medium',
    }

    results = session.query(
        ProcurementProcedure.type,
        func.count(Award.id).label('count'),
        func.sum(Award.value).label('total_value')
    ).join(Award).group_by(ProcurementProcedure.type).all()

    data = []
    for proc_type, count, total_value in results:
        if proc_type:
            data.append({
                "type": proc_type,
                "count": count,
                "total_value": float(total_value or 0),
                "risk_level": risk_mapping.get(proc_type, 'medium')
            })

    return sorted(data, key=lambda x: x['count'], reverse=True)


@router.get("/stats/top-suppliers")
def get_top_suppliers(limit: int = 15, session: Session = Depends(get_session)):
    """Get top suppliers by total contract value"""

    results = session.query(
        Supplier.id,
        Supplier.name,
        Supplier.country,
        func.count(Award.id).label('contract_count'),
        func.sum(Award.value).label('total_value')
    ).join(
        Award, Award.id == Supplier.id  # This needs proper join via award_supplier table
    ).group_by(
        Supplier.id, Supplier.name, Supplier.country
    ).order_by(
        desc('total_value')
    ).limit(limit).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "country": r.country,
            "contract_count": r.contract_count,
            "total_value": float(r.total_value or 0)
        }
        for r in results
    ]


@router.get("/stats/top-authorities")
def get_top_authorities(limit: int = 15, session: Session = Depends(get_session)):
    """Get top contracting authorities by total spending"""

    results = session.query(
        ContractingAuthority.id,
        ContractingAuthority.name,
        ContractingAuthority.city,
        func.count(Award.id).label('contract_count'),
        func.sum(Award.value).label('total_value')
    ).join(Award).group_by(
        ContractingAuthority.id,
        ContractingAuthority.name,
        ContractingAuthority.city
    ).order_by(
        desc('total_value')
    ).limit(limit).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "city": r.city,
            "contract_count": r.contract_count,
            "total_value": float(r.total_value or 0)
        }
        for r in results
    ]


@router.get("/stats/suppliers-by-country")
def get_suppliers_by_country(limit: int = 15, session: Session = Depends(get_session)):
    """Get supplier distribution by country"""

    results = session.query(
        Supplier.country,
        func.count(Supplier.id).label('supplier_count'),
        func.sum(Award.value).label('total_value')
    ).join(
        Award, Award.id == Supplier.id
    ).group_by(
        Supplier.country
    ).order_by(
        desc('total_value')
    ).limit(limit).all()

    return [
        {
            "country": r.country or "Unknown",
            "supplier_count": r.supplier_count,
            "total_value": float(r.total_value or 0)
        }
        for r in results
    ]


@router.get("/stats/competition-analysis")
def get_competition_analysis(session: Session = Depends(get_session)):
    """Analyze competition levels (number of bids)"""

    # Group by number of bids
    results = session.query(
        Award.number_of_received_offers,
        func.count(Award.id).label('count'),
        func.sum(Award.value).label('total_value')
    ).filter(
        Award.number_of_received_offers.isnot(None)
    ).group_by(
        Award.number_of_received_offers
    ).order_by(
        Award.number_of_received_offers
    ).all()

    data = []
    for bids, count, total_value in results:
        risk_level = 'high' if bids <= 1 else ('medium' if bids <= 3 else 'low')
        data.append({
            "bids": bids,
            "count": count,
            "total_value": float(total_value or 0),
            "risk_level": risk_level
        })

    return data


@router.get("/stats/top-owners")
def get_top_owners(limit: int = 15, session: Session = Depends(get_session)):
    """Get individuals with most company ownership"""

    try:
        # Count company ownership by person (excluding companies)
        results = session.query(
            CompanyRelation.full_name,
            func.count(func.distinct(CompanyRelation.company_record_id)).label('company_count')
        ).filter(
            CompanyRelation.full_name.isnot(None),
            CompanyRelation.full_name != '',
            # Exclude companies (usually contain d.o.o, LLC, etc)
            ~CompanyRelation.full_name.ilike('%d.o.o%'),
            ~CompanyRelation.full_name.ilike('%LLC%'),
            ~CompanyRelation.full_name.ilike('%Ltd%'),
            ~CompanyRelation.full_name.ilike('%Inc%'),
            ~CompanyRelation.full_name.ilike('%Corp%'),
            ~CompanyRelation.full_name.ilike('%a.d.%'),
        ).group_by(
            CompanyRelation.full_name
        ).order_by(
            desc('company_count')
        ).limit(limit).all()

        if not results:
            return []

        total_companies = session.query(func.count(func.distinct(Company.id))).scalar() or 1

        return [
            {
                "name": r.full_name,
                "company_count": r.company_count,
                "ownership_percentage": round(r.company_count / total_companies * 100, 2)
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error in get_top_owners: {e}")
        return []