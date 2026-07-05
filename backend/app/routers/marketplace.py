"""B2B/B2C agribusiness marketplace endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import ROLE_BUYER, ROLE_FARMER, Listing, User
from app.schemas import ListingCreate, ListingOut

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

# Which listing_type each role publishes:
#   farmer (producer) -> "sell" offers (produce, tools, inputs for sale)
#   buyer  (consumer) -> "buy"  requests ("wanted" ads)
ROLE_LISTING_TYPE = {ROLE_FARMER: "sell", ROLE_BUYER: "buy"}
# The complementary feed each role wants to see (connect buyers <-> sellers):
ROLE_FEED_TYPE = {ROLE_FARMER: "buy", ROLE_BUYER: "sell"}


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


@router.get("/feed", response_model=list[ListingOut])
def role_feed(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
):
    """Role-synced feed: buyers see produce for sale, farmers see buyer requests."""
    wanted = ROLE_FEED_TYPE.get(current.role, "sell")
    return (
        db.query(Listing)
        .filter(Listing.status == "active", Listing.listing_type == wanted)
        .order_by(Listing.created_at.desc())
        .limit(limit)
        .all()
    )


@router.post("/listings", response_model=ListingOut, status_code=201)
def create_listing(
    payload: ListingCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    # The listing_type is derived from the user's role so producers publish
    # "sell" offers and consumers publish "buy" requests — keeping the two
    # sides of the marketplace cleanly in sync.
    data["listing_type"] = ROLE_LISTING_TYPE.get(current.role, "sell")
    listing = Listing(seller_id=current.id, **data)
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
