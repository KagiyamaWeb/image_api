import boto3

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Form
from fastapi.websockets import WebSocket, WebSocketDisconnect
from typing import List
from sqlalchemy.orm import Session
from botocore.exceptions import NoCredentialsError
from app.models import Base, ImageModel
from app.schemas import UploadResponse, ImageResponse
from app.crud import create_image, get_images_by_project
from app.config import get_db, engine
from app.s3_utils import generate_presigned_url, upload_file
from app.tasks import process_image

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

app = FastAPI()
Base.metadata.create_all(bind=engine)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
    return UploadResponse(image_id=image.id, upload_link=upload_url)


@app.get("/projects/{project_id}/images", response_model=List[ImageResponse])
def read_images(project_id: int, db: Session = Depends(get_db)):
    images = get_images_by_project(db, project_id=project_id)
    return images