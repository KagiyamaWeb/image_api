from app.celery_worker import celery
from app.s3_utils import s3_client, BUCKET_NAME
from app.config import SessionLocal
from app.models import ImageModel
from PIL import Image
import os


@celery.task
def check_new_uploads():
    db = SessionLocal()
    images = db.query(ImageModel).filter(ImageModel.state == "init").all()
    for image in images:
        try:
            s3_client.head_object(Bucket=BUCKET_NAME, Key=image.filename)
            process_image.delay(image.id)
        except Exception as e:
            continue
    db.close()

@celery.task
def process_image(image_id: int):
    db = SessionLocal()
    image = db.query(ImageModel).filter(ImageModel.id == image_id).first()
    if not image:
        return

    # Download the image from S3
    s3_client.download_file(BUCKET_NAME, image.filename, image.filename)

    # Process image and upload different versions
    versions = {
        "thumb": (150, 120),
        "big_thumb": (700, 700),
        "big_1920": (1920, 1080),
        "d2500": (2500, 2500)
    }

    for version, size in versions.items():
        with Image.open(image.filename) as img:
            img.thumbnail(size, Image.ANTIALIAS)
            version_filename = f"{version}_{image.filename}"
            img.save(version_filename)

            # Upload to S3
            s3_client.upload_file(version_filename, BUCKET_NAME, version_filename)

            # Update database with URL
            url = f"http://minio:9000/{BUCKET_NAME}/{version_filename}"
            setattr(image, f"{version}_url", url)

            os.remove(version_filename)

    image.state = "done"
    db.commit()
    db.close()