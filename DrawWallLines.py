import cv2
import numpy as np
import os
import io
import json
import logging
import base64
from azure.storage.blob import BlobServiceClient

def annotate_and_save_image(image, blob_name, connect_string, lines=None):
    """
    Annotate the image with lines and save to Azure Blob Storage.
    Args:
        image: np.ndarray, the image to annotate.
        blob_name: str, original blob name.
        connect_string: str, Azure Blob Storage connection string.
        lines: list of line coordinates, e.g., [[x1, y1, x2, y2], ...]
    """

    logging.info(f"Image shape: {image.shape if image is not None else 'None'}")
    if image is not None:
        logging.info(f"Start drawing lines on image: {blob_name}")

        # If no lines provided, use OpenCV to detect lines automatically
        if not lines:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            # Hough Line Transform
            detected_lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)
            lines = []
            if detected_lines is not None:
                for line in detected_lines:
                    x1, y1, x2, y2 = line[0]
                    lines.append([x1, y1, x2, y2])
            logging.info(f"Auto-detected {len(lines)} lines using OpenCV.")

        # Draw lines on the image
        annotated_image = image.copy()
        for line in lines:
            if len(line) == 4:
                x1, y1, x2, y2 = line
                cv2.line(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        _, img_encoded = cv2.imencode('.png', annotated_image)
        # Save to output blob (e.g., 'pdf-images/annotated_{blob_name}')
        logging.info(f"Saving annotated image to blob storage: {blob_name}")
        blob_service_client = BlobServiceClient.from_connection_string(connect_string)
        blob_client = blob_service_client.get_blob_client(container="pdf-images", blob=f"annotated_{blob_name}")
        blob_client.upload_blob(img_encoded.tobytes(), overwrite=True)
        logging.info(f"Annotated image saved as: annotated_{blob_name}")
    else:
        logging.error("Failed to decode image")
