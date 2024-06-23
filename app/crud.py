from sqlalchemy.orm import Session
from app.models import ImageModel
from app.schemas import ImageCreate

def create_image(db: Session, project_id: int, filename: str):
    db_image = ImageModel(project_id=project_id, filename=filename, state="init")
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def get_images_by_project(db: Session, project_id: int):
    return db.query(ImageModel).filter(ImageModel.project_id == project_id).all()