import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
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

def test_create_upload_image(test_app):
    response = test_app.post("/images/", data={"project_id": 1, "filename": "test.jpg"})
    assert response.status_code == 200
    response_data = response.json()
    assert "image_id" in response_data
    assert "upload_link" in response_data

@patch("app.s3_utils.upload_file", return_value=True)
@patch("app.tasks.process_image.delay", return_value=None)
def test_upload_image(mock_process_image, mock_upload_file, test_app):
    # Create an image entry
    response = test_app.post("/images/", data={"project_id": 1, "filename": "test.jpg"})
    image_id = response.json()["image_id"]

    # Upload a file
    with open("tests/test_image.jpg", "rb") as file:
        response = test_app.post(f"/upload/{image_id}", files={"file": file})
    assert response.status_code == 200
    assert response.json() == {"info": "File uploaded successfully"}

    # Verify Celery task was called
    mock_process_image.assert_called_once_with(image_id)

def test_read_images(test_app):
    # Create an image entry
    response = test_app.post("/images/", data={"project_id": 1, "filename": "test.jpg"})
    image_id = response.json()["image_id"]

    # Retrieve images by project_id
    response = test_app.get("/projects/1/images")
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert any(image["image_id"] == image_id for image in response_data)

def test_process_image():
    from app.tasks import process_image
    from app.config import SessionLocal

    # Create an image entry
    db = SessionLocal()
    image = ImageModel(project_id=1, filename="test.jpg", state="uploaded", original_url="http://example.com/test.jpg")
    db.add(image)
    db.commit()
    db.refresh(image)

    # Run the Celery task synchronously
    process_image(image.id)

    # Verify the image state is updated and URLs are set
    updated_image = db.query(ImageModel).filter(ImageModel.id == image.id).first()
    assert updated_image.state == "done"
    assert updated_image.thumb_url is not None
    assert updated_image.big_thumb_url is not None
    assert updated_image.big_1920_url is not None
    assert updated_image.d2500_url is not None

    db.delete(updated_image)
    db.commit()
    db.close()