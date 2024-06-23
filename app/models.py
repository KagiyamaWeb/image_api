from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class ImageModel(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    project_id = Column(Integer, index=True)
    state = Column(String, default="init")
    original_url = Column(String, nullable=True, default=None)
    thumb_url = Column(String, nullable=True, default=None)
    big_thumb_url = Column(String, nullable=True, default=None)
    big_1920_url = Column(String, nullable=True, default=None)
    d2500_url = Column(String, nullable=True, default=None)