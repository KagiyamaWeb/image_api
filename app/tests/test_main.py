import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import websockets
from app.main import app, get_db
from app.config import SessionLocal
from app.celery_worker import process_image
from app.config import Base
from unittest.mock import patch
from app.models import ImageModel

DATABASE_URL = "sqlite:///./test.db"  # Use an in-memory SQLite database for testing
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def test_app():
    with TestClient(app) as client:
        yield client

@pytest.mark.asyncio
async def test_create_upload_image(test_app):
    response = await test_app.post("/images/", data={"project_id": 1, "filename": "test.jpg"})
    assert response.status_code == 200
    response_data = response.json()
    assert "image_id" in response_data
    assert "upload_link" in response_data

@pytest.mark.asyncio
async def test_read_images(test_app):
    # Create an image entry
    response = test_app.post("/images/", data={"project_id": 1, "filename": "test.jpg"})
    image_id = response.json()["image_id"]

    # Retrieve images by project_id
    response = test_app.get("/projects/1/images")
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert any(image["image_id"] == image_id for image in response_data)

@pytest.mark.asyncio
async def test_process_image_task():
    db = SessionLocal()
    image = ImageModel(filename="test.jpg", project_id=1)
    db.add(image)
    db.commit()
    db.refresh(image)
    await process_image(image.id)
    db.refresh(image)
    assert image.state == "done"
    assert image.thumb_url is not None
    assert image.big_thumb_url is not None
    assert image.big_1920_url is not None
    assert image.d2500_url is not None
    db.close()

@pytest.mark.asyncio
async def test_websocket_notification():
    async with websockets.connect('ws://localhost:8000/ws') as websocket:
        await websocket.send("Test message")
        response = await websocket.recv()
        assert "You wrote: Test message" in response