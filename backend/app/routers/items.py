import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.item import LostItem, FoundItem, ItemImage
from app.schemas.item import (
    LostItemCreate,
    FoundItemCreate,
    LostItemOut,
    FoundItemOut,
    ItemStatusUpdate,
    ImageUploadResponse,
    UserReportsResponse,
    ItemStatsResponse,
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/items", tags=["Items Management"])

# Permitted upload extensions & MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif"
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def serialize_lost_item(item: LostItem) -> LostItemOut:
    user_name = item.user.full_name if item.user else None
    return LostItemOut(
        id=item.id,
        user_id=item.user_id,
        title=item.title,
        category=item.category,
        description=item.description,
        color=item.color,
        brand=item.brand,
        model=item.model,
        location=item.location,
        date_lost=item.date_lost,
        distinctive_features=item.distinctive_features,
        extracted_tags=item.extracted_tags,
        image_url=item.image_url,
        status=item.status,
        created_at=item.created_at,
        user_name=user_name
    )


def serialize_found_item(item: FoundItem) -> FoundItemOut:
    user_name = item.user.full_name if item.user else None
    return FoundItemOut(
        id=item.id,
        user_id=item.user_id,
        title=item.title,
        category=item.category,
        description=item.description,
        color=item.color,
        brand=item.brand,
        model=item.model,
        location=item.location,
        date_found=item.date_found,
        distinctive_features=item.distinctive_features,
        extracted_tags=item.extracted_tags,
        image_url=item.image_url,
        status=item.status,
        created_at=item.created_at,
        user_name=user_name
    )


# -----------------------------------------------------------------------------
# Image Upload
# -----------------------------------------------------------------------------
@router.post("/upload-image", response_model=ImageUploadResponse)
async def upload_item_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    content_type = file.content_type.lower() if file.content_type else ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Only JPG, PNG, WEBP, and GIF images are supported."
        )

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Generate unique filename
    ext = ALLOWED_MIME_TYPES[content_type]
    filename = f"item_{uuid.uuid4().hex[:16]}_{int(func.now().compile().params.get('now', 0) if False else uuid.uuid1().time)}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    # Read and validate size
    try:
        contents = await file.read()
        file_size = len(contents)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum limit of 10MB ({file_size / (1024 * 1024):.2f}MB provided)."
            )
        with open(file_path, "wb") as f:
            f.write(contents)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(exc)}"
        )
    finally:
        await file.close()

    image_url = f"/uploads/{filename}"
    return ImageUploadResponse(
        filename=filename,
        image_url=image_url,
        content_type=content_type,
        size_bytes=file_size
    )


# -----------------------------------------------------------------------------
# Lost Items Endpoints
# -----------------------------------------------------------------------------
@router.post("/lost", response_model=LostItemOut, status_code=status.HTTP_201_CREATED)
def report_lost_item(
    item_data: LostItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_item = LostItem(
        user_id=current_user.id,
        title=item_data.title.strip(),
        category=item_data.category.strip(),
        description=item_data.description.strip(),
        color=item_data.color.strip() if item_data.color else None,
        brand=item_data.brand.strip() if item_data.brand else None,
        model=item_data.model.strip() if item_data.model else None,
        location=item_data.location.strip(),
        date_lost=item_data.date_lost.strip(),
        distinctive_features=item_data.distinctive_features,
        image_url=item_data.image_url.strip() if item_data.image_url else None,
        status="active"
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return serialize_lost_item(new_item)


@router.get("/lost", response_model=List[LostItemOut])
def get_lost_items(
    search: Optional[str] = Query(None, description="Search term for title, description, brand, location"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by location"),
    status: Optional[str] = Query(None, description="Filter by status (active, matched, returned, or all)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(LostItem)

    if status and status.lower() != "all":
        query = query.filter(LostItem.status == status.lower())

    if category and category.lower() != "all":
        query = query.filter(func.lower(LostItem.category) == category.lower())

    if location and location.strip():
        query = query.filter(LostItem.location.ilike(f"%{location.strip()}%"))

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                LostItem.title.ilike(term),
                LostItem.description.ilike(term),
                LostItem.brand.ilike(term),
                LostItem.model.ilike(term),
                LostItem.color.ilike(term),
                LostItem.location.ilike(term),
            )
        )

    items = query.order_by(desc(LostItem.created_at)).offset(skip).limit(limit).all()
    return [serialize_lost_item(item) for item in items]


@router.get("/lost/{item_id}", response_model=LostItemOut)
def get_lost_item_by_id(item_id: int, db: Session = Depends(get_db)):
    item = db.query(LostItem).filter(LostItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lost item with ID {item_id} not found"
        )
    return serialize_lost_item(item)


@router.patch("/lost/{item_id}/status", response_model=LostItemOut)
def update_lost_item_status(
    item_id: int,
    status_update: ItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(LostItem).filter(LostItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lost item with ID {item_id} not found"
        )

    # Permission check: owner or admin
    if item.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this item"
        )

    item.status = status_update.status.lower()
    db.commit()
    db.refresh(item)
    return serialize_lost_item(item)


@router.delete("/lost/{item_id}", status_code=status.HTTP_200_OK)
def delete_lost_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(LostItem).filter(LostItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lost item with ID {item_id} not found"
        )

    if item.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this item"
        )

    db.delete(item)
    db.commit()
    return {"detail": "Lost item deleted successfully", "id": item_id}


# -----------------------------------------------------------------------------
# Found Items Endpoints
# -----------------------------------------------------------------------------
@router.post("/found", response_model=FoundItemOut, status_code=status.HTTP_201_CREATED)
def report_found_item(
    item_data: FoundItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_item = FoundItem(
        user_id=current_user.id,
        title=item_data.title.strip(),
        category=item_data.category.strip(),
        description=item_data.description.strip(),
        color=item_data.color.strip() if item_data.color else None,
        brand=item_data.brand.strip() if item_data.brand else None,
        model=item_data.model.strip() if item_data.model else None,
        location=item_data.location.strip(),
        date_found=item_data.date_found.strip(),
        distinctive_features=item_data.distinctive_features,
        image_url=item_data.image_url.strip() if item_data.image_url else None,
        status="active"
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return serialize_found_item(new_item)


@router.get("/found", response_model=List[FoundItemOut])
def get_found_items(
    search: Optional[str] = Query(None, description="Search term for title, description, brand, location"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by location"),
    status: Optional[str] = Query(None, description="Filter by status (active, matched, returned, or all)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(FoundItem)

    if status and status.lower() != "all":
        query = query.filter(FoundItem.status == status.lower())

    if category and category.lower() != "all":
        query = query.filter(func.lower(FoundItem.category) == category.lower())

    if location and location.strip():
        query = query.filter(FoundItem.location.ilike(f"%{location.strip()}%"))

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                FoundItem.title.ilike(term),
                FoundItem.description.ilike(term),
                FoundItem.brand.ilike(term),
                FoundItem.model.ilike(term),
                FoundItem.color.ilike(term),
                FoundItem.location.ilike(term),
            )
        )

    items = query.order_by(desc(FoundItem.created_at)).offset(skip).limit(limit).all()
    return [serialize_found_item(item) for item in items]


@router.get("/found/{item_id}", response_model=FoundItemOut)
def get_found_item_by_id(item_id: int, db: Session = Depends(get_db)):
    item = db.query(FoundItem).filter(FoundItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Found item with ID {item_id} not found"
        )
    return serialize_found_item(item)


@router.patch("/found/{item_id}/status", response_model=FoundItemOut)
def update_found_item_status(
    item_id: int,
    status_update: ItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(FoundItem).filter(FoundItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Found item with ID {item_id} not found"
        )

    if item.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this item"
        )

    item.status = status_update.status.lower()
    db.commit()
    db.refresh(item)
    return serialize_found_item(item)


@router.delete("/found/{item_id}", status_code=status.HTTP_200_OK)
def delete_found_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(FoundItem).filter(FoundItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Found item with ID {item_id} not found"
        )

    if item.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this item"
        )

    db.delete(item)
    db.commit()
    return {"detail": "Found item deleted successfully", "id": item_id}


# -----------------------------------------------------------------------------
# User Dashboard Reports & Global Statistics
# -----------------------------------------------------------------------------
@router.get("/my-reports", response_model=UserReportsResponse)
def get_user_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lost_items = (
        db.query(LostItem)
        .filter(LostItem.user_id == current_user.id)
        .order_by(desc(LostItem.created_at))
        .all()
    )
    found_items = (
        db.query(FoundItem)
        .filter(FoundItem.user_id == current_user.id)
        .order_by(desc(FoundItem.created_at))
        .all()
    )

    return UserReportsResponse(
        lost_items=[serialize_lost_item(item) for item in lost_items],
        found_items=[serialize_found_item(item) for item in found_items],
        total_lost=len(lost_items),
        total_found=len(found_items)
    )


@router.get("/stats", response_model=ItemStatsResponse)
def get_item_stats(db: Session = Depends(get_db)):
    total_lost = db.query(func.count(LostItem.id)).scalar() or 0
    active_lost = db.query(func.count(LostItem.id)).filter(LostItem.status == "active").scalar() or 0
    total_found = db.query(func.count(FoundItem.id)).scalar() or 0
    active_found = db.query(func.count(FoundItem.id)).filter(FoundItem.status == "active").scalar() or 0
    resolved_lost = db.query(func.count(LostItem.id)).filter(LostItem.status.in_(["matched", "returned"])).scalar() or 0
    resolved_found = db.query(func.count(FoundItem.id)).filter(FoundItem.status.in_(["matched", "returned"])).scalar() or 0

    return ItemStatsResponse(
        total_lost=total_lost,
        active_lost=active_lost,
        total_found=total_found,
        active_found=active_found,
        total_resolved=resolved_lost + resolved_found
    )
