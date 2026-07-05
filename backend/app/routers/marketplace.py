"""B2B/B2C agribusiness marketplace endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Listing, User
from app.schemas import ListingCreate, ListingOut

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


@router.get("/listings", response_model=list[ListingOut])
def list_listings(
    category: str | None = None,
    listing_type: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
):
    q = db.query(Listing).filter(Listing.status == "active")
    if category:
        q = q.filter(Listing.category == category)
    if listing_type:
        q = q.filter(Listing.listing_type == listing_type)
    if search:
        like = f"%{search}%"
        q = q.filter(Listing.title.ilike(like) | Listing.description.ilike(like))
    return q.order_by(Listing.created_at.desc()).limit(limit).all()


@router.post("/listings", response_model=ListingOut, status_code=201)
def create_listing(
    payload: ListingCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = Listing(seller_id=current.id, **payload.model_dump())
    if not listing.location:
        listing.location = current.location
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/listings/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get("/my-listings", response_model=list[ListingOut])
def my_listings(
    current: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Listing)
        .filter(Listing.seller_id == current.id)
        .order_by(Listing.created_at.desc())
        .all()
    )


@router.delete("/listings/{listing_id}", status_code=204)
def delete_listing(
    listing_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != current.id:
        raise HTTPException(status_code=403, detail="Not your listing")
    db.delete(listing)
    db.commit()
