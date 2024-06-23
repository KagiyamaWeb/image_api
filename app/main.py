import boto3

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Form
from typing import List
from sqlalchemy.orm import Session
from botocore.exceptions import NoCredentialsError
from app.models import Base, ImageModel
from app.schemas import UploadResponse, ImageResponse
from app.crud import create_image, get_images_by_project
from app.config import get_db, engine
from app.s3_utils import generate_presigned_url, upload_file
from app.tasks import process_image

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.post("/images/", response_model=UploadResponse)
def create_upload_image(
    project_id: int = Form(...), 
    filename: str = Form(...), 
    db: Session = Depends(get_db)
):
    image = create_image(db, project_id=project_id, filename=filename)
    upload_url = generate_presigned_url(filename)
    if not upload_url:
        raise HTTPException(status_code=500, detail="Error generating presigned URL")
    #return {"image_id": image.id, "upload_link": upload_url}
    return UploadResponse(image_id=image.id, upload_link=upload_url)

@app.post("/upload/{image_id}")
async def upload_image(
    image_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    image = db.query(ImageModel).filter(ImageModel.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(file.file.read())
    
    success = upload_file(file_location, image.filename)
    if not success:
        raise HTTPException(status_code=500, detail="Error uploading file to S3")

    image.state = "uploaded"
    db.commit()

    # Trigger image processing
    process_image.delay(image.id)

    return {"info": "File uploaded successfully"}

@app.get("/projects/{project_id}/images", response_model=List[ImageResponse])
def read_images(project_id: int, db: Session = Depends(get_db)):
    images = get_images_by_project(db, project_id=project_id)
    return images