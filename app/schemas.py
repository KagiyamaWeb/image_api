from pydantic import BaseModel
from typing import Optional


class ImageCreate(BaseModel):
    filename: str
    project_id: int

class UploadResponse(BaseModel):
    image_id: int
    upload_link: str

class ImageResponse(BaseModel):
    id: int
    filename: str
    project_id: int
    state: str
    original_url: Optional[str] = None
    thumb_url: Optional[str] = None
    big_thumb_url: Optional[str] = None
    big_1920_url: Optional[str] = None
    d2500_url: Optional[str] = None

    class Config:
        orm_mode = True