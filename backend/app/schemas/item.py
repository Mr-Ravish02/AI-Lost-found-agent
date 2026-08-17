from pydantic import BaseModel, Field
from typing import Optional, List, Any, Union
from datetime import datetime


class LostItemCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=3)
    color: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    location: str = Field(..., min_length=2, max_length=200)
    date_lost: str = Field(..., min_length=4, max_length=30)
    distinctive_features: Optional[Union[List[str], str]] = None
    image_url: Optional[str] = None


class FoundItemCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=3)
    color: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    location: str = Field(..., min_length=2, max_length=200)
    date_found: str = Field(..., min_length=4, max_length=30)
    distinctive_features: Optional[Union[List[str], str]] = None
    image_url: Optional[str] = None


class LostItemOut(BaseModel):
    id: int
    user_id: int
    title: str
    category: str
    description: str
    color: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    location: str
    date_lost: str
    distinctive_features: Optional[Any] = None
    extracted_tags: Optional[Any] = None
    image_url: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class FoundItemOut(BaseModel):
    id: int
    user_id: int
    title: str
    category: str
    description: str
    color: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    location: str
    date_found: str
    distinctive_features: Optional[Any] = None
    extracted_tags: Optional[Any] = None
    image_url: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class ItemStatusUpdate(BaseModel):
    status: str = Field(..., min_length=3, max_length=30)


class ImageUploadResponse(BaseModel):
    filename: str
    image_url: str
    content_type: str
    size_bytes: int


class UserReportsResponse(BaseModel):
    lost_items: List[LostItemOut]
    found_items: List[FoundItemOut]
    total_lost: int
    total_found: int


class ItemStatsResponse(BaseModel):
    total_lost: int
    active_lost: int
    total_found: int
    active_found: int
    total_resolved: int
