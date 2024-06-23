import aiohttp
import aiofiles
import asyncio
import os
import logging

from app.celery_worker import celery
from app.s3_utils import s3_client, BUCKET_NAME
from app.config import SessionLocal
from app.models import ImageModel
from PIL import Image


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def download_image(url: str, filename: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(filename, 'wb') as f:
                    await f.write(await response.read())
            else:
                logger.error(f"Failed to download image from {url}")

@celery.task
def process_image(image_id: int):
    db = SessionLocal()
    image = db.query(ImageModel).filter(ImageModel.id == image_id).first()
    original_filename = image.filename
    image_url = image.original_url

    logger.info(f"Starting to process image {image_id}")

    try:
        # Download original image
        loop = asyncio.get_event_loop()
        loop.run_until_complete(download_image(image_url, original_filename))

        # Create different versions
        versions = {
            "thumb": (150, 120),
            "big_thumb": (700, 700),
            "big_1920": (1920, 1080),
            "d2500": (2500, 2500)
        }

        for version, size in versions.items():
            version_filename = f"{version}_{original_filename}"
            with Image.open(original_filename) as img:
                img.thumbnail(size, Image.ANTIALIAS)
                img.save(version_filename)

                # Upload to S3
                s3_client.upload_file(version_filename, BUCKET_NAME, version_filename)
                logger.info(f"Uploaded {version_filename} to {BUCKET_NAME}")

                # Update database with URL
                setattr(image, f"{version}_url", f"http://minio:9000/{BUCKET_NAME}/{version_filename}")

        image.state = "done"
        db.commit()
        logger.info(f"Finished processing image {image_id}")

    except Exception as e:
        logger.error(f"Error processing image {image_id}: {e}")
    finally:
        db.close()