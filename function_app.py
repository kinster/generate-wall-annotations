import cv2
import numpy as np
import os
import io
import json
import logging
import base64
import azure.functions as func

from DrawWallLines import annotate_and_save_image

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="annotatewalls")
@app.route(route="annotatewalls", methods=["POST"])
def ExtractScale(req: func.HttpRequest) -> func.HttpResponse:
    try:

        data = req.get_json()

        base64_img = data["base64"]

        logging.info('Python HTTP trigger function processed a request.')

        connect_string = os.environ["AzureWebJobsStorage"]
        blob_name = "from_http_request.png"  # Or generate a unique name

        if "," in base64_img:
            base64_img = base64_img.split(",")[1]
        image_bytes = base64.b64decode(base64_img)

        image_array = np.frombuffer(image_bytes, dtype=np.uint8)

        logging.info(f"Image buffer length: {len(image_array)}")

        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        lines = [[100, 100, 200, 200]]  # Example lines

        annotate_and_save_image(image, blob_name, connect_string, lines)

        logging.info(f"Status finished")
        # ✅ Wrap the dict in HttpResponse
        return func.HttpResponse(
            body=json.dumps({"status": "done"}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )

@app.function_name(name="blobtrigger")
@app.blob_trigger(arg_name="blob",
                  path="pdf-images/{name}",
                  connection="AzureWebJobsStorage")
def run_blob_trigger(blob: func.InputStream):
    connect_string = os.environ["AzureWebJobsStorage"]
    logging.info(f"connect_string: {connect_string}")
    logging.info(f"Blob trigger fired for: {blob.name}")
    logging.info(f"Blob size: {blob.length} bytes")
    blob_data = blob.read()
    image = cv2.imdecode(np.frombuffer(blob_data, np.uint8), cv2.IMREAD_COLOR)
    # Example lines to draw
    lines = [[100, 100, 200, 200]]

    annotate_and_save_image(image, blob.name, connect_string, lines)
