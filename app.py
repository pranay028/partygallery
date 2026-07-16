import os
import uuid
import threading
from dotenv import load_dotenv
from google.cloud import storage
from flask import (
    Flask,
    render_template,
    flash,
    request,
    redirect,
    url_for,
    jsonify,
)
from datetime import timedelta
import google.auth
from google.auth.transport import requests as google_auth_requests
from PIL import Image
import io
import pillow_heif
# This registers the HEIC format so Image.open() recognizes it
pillow_heif.register_heif_opener()



SERVICE_ACCOUNT_EMAIL = "partyphotoslocal@partyphotos-501522.iam.gserviceaccount.com"

load_dotenv()

if not os.getenv("K_SERVICE"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/pranay/Desktop/partyphotos/service-account.json"

credentials, project = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

PROJECT_ID = project
BUCKET_NAME = os.getenv("BUCKET_NAME")

storage_client = storage.Client(project=PROJECT_ID)

app = Flask(__name__)
app.secret_key = os.getenv("APP_FLASK_SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024







def generate_thumbnail_in_background(file_bytes, unique_filename, bucket_name, project_id):
    try:
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)

        img = Image.open(io.BytesIO(file_bytes))

        original_width, original_height = img.size

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail((400, 400))

        thumb_io = io.BytesIO()

        img.save(
            thumb_io,
            format='JPEG',
            quality=80
        )

        thumb_io.seek(0)

        thumb_blob = bucket.blob(
            f"thumbnails/{unique_filename}"
        )

        thumb_blob.metadata = {
            "width": str(original_width),
            "height": str(original_height)
        }

        thumb_blob.upload_from_file(
            thumb_io,
            content_type='image/jpeg'
        )

        thumb_blob.patch()

    except Exception as e:
        print(f"DEBUG: Background thumbnail failed: {e}")






@app.route('/images')
def images():

    bucket = storage_client.bucket(BUCKET_NAME)

    all_blobs = list(bucket.list_blobs(prefix='images/'))

    file_blobs = [
        b for b in all_blobs
        if not b.name.endswith('/')
    ]

    file_blobs.sort(
        key=lambda x: x.time_created,
        reverse=True
    )


    images_data = []


    for blob in file_blobs:

        filename = blob.name.split('/')[-1]


        width = 1
        height = 1


        try:
            # Get thumbnail metadata
            thumb_blob = bucket.blob(
                f"thumbnails/{filename}"
            )

            thumb_blob.reload()

            if thumb_blob.metadata:

                width = int(
                    thumb_blob.metadata.get(
                        "width",
                        1
                    )
                )

                height = int(
                    thumb_blob.metadata.get(
                        "height",
                        1
                    )
                )


        except Exception as e:

            print(
                "Could not read image metadata:",
                e
            )


        images_data.append({

            'original':
                f"https://storage.googleapis.com/{BUCKET_NAME}/images/{filename}",

            'thumbnail':
                f"https://storage.googleapis.com/{BUCKET_NAME}/thumbnails/{filename}",

            'width':
                width,

            'height':
                height

        })


    return render_template(
        'images.html',
        images=images_data
    )






@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    bucket = storage_client.bucket(BUCKET_NAME)
    for file in files:
        if not file or not file.filename : continue
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_bytes = file.read()
        blob = bucket.blob(f"images/{unique_filename}")
        blob.upload_from_string(file_bytes, content_type=file.content_type)
        thread = threading.Thread(
            target=generate_thumbnail_in_background, 
            args=(file_bytes, unique_filename, BUCKET_NAME, PROJECT_ID)
        )
        thread.start()
    return redirect(url_for('index'))


    

@app.route('/videos')
def videos():
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # Fetch ALL blobs (or a large enough subset)
    blobs = list(bucket.list_blobs(prefix='videos/'))
    
    # Sort the entire list in memory
    blobs.sort(key=lambda x: x.time_created, reverse=True)
    
    # You can now manually slice the list if you really want "pages"
    return render_template('videos.html', videos=blobs, bucket_name=BUCKET_NAME)




@app.route('/')
def index():
    bucket = storage_client.bucket(BUCKET_NAME)
    all_blobs = list(bucket.list_blobs(prefix='images/'))
    file_blobs = [b for b in all_blobs if not b.name.endswith('/')]
    file_blobs.sort(key=lambda x: x.time_created, reverse=True)
    
    images_data = []
    for blob in file_blobs:
        filename = blob.name.split('/')[-1] 
        images_data.append({
            'original': f"https://storage.googleapis.com/{BUCKET_NAME}/images/{filename}",
            'thumbnail': f"https://storage.googleapis.com/{BUCKET_NAME}/thumbnails/{filename}"
        })
    return render_template('index.html', images=images_data[:4])




@app.route('/get-signed-url')
def get_signed_url():
    filename = request.args.get('filename')
    content_type = request.args.get('content_type')
    
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"videos/{filename}")

    # 1. Grab the default credentials (the Cloud Run environment identity)


    auth_request = google_auth_requests.Request()
    credentials.refresh(auth_request)
    
    # 3. Ask Google's IAM service to sign the URL using the token we just grabbed
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="PUT",
        content_type=content_type,
        service_account_email=SERVICE_ACCOUNT_EMAIL,
        access_token=credentials.token  # <--- THIS IS THE MAGIC MISSING PIECE
    )
    return jsonify({"url": url})






@app.errorhandler(413)
def request_entity_too_large(error):
    return 'File too large! Max is 500MB', 413

if __name__ == '__main__':

    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(
        host="0.0.0.0",
        port=8080,
        debug=debug_mode
    )