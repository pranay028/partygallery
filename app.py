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
    session
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


ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")




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
    # Get the page number from the URL (default to page 1)
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Limit to 20 images per page
    
    bucket = storage_client.bucket(BUCKET_NAME)
    all_blobs = list(bucket.list_blobs(prefix='images/'))
    file_blobs = [b for b in all_blobs if not b.name.endswith('/')]
    
    # Sort newest first
    file_blobs.sort(key=lambda x: x.time_created, reverse=True)
    
    # Calculate exactly which 20 blobs to process based on the page number
    total_images = len(file_blobs)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Slice the list! (This is the magic that saves server time)
    paginated_blobs = file_blobs[start_idx:end_idx]

    images_data = []
    for blob in paginated_blobs:
        filename = blob.name.split('/')[-1]
        width = 1
        height = 1

        try:
            # Get thumbnail metadata
            thumb_blob = bucket.blob(f"thumbnails/{filename}")
            thumb_blob.reload()
            if thumb_blob.metadata:
                width = int(thumb_blob.metadata.get("width", 1))
                height = int(thumb_blob.metadata.get("height", 1))
        except Exception as e:
            print("Could not read image metadata:", e)

        images_data.append({
            'original': f"https://storage.googleapis.com/{BUCKET_NAME}/images/{filename}",
            'thumbnail': f"https://storage.googleapis.com/{BUCKET_NAME}/thumbnails/{filename}",
            'width': width,
            'height': height
        })

    # Check if there are more images after this page
    has_next = end_idx < total_images
    next_page = page + 1 if has_next else None

    return render_template(
    'images.html',
    images=images_data,
    next_page=next_page,
    current_page=page,
    total_images=total_images
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

    videos = list(
        bucket.list_blobs(
            prefix='videos/'
        )
    )

    videos = [
        video
        for video in videos
        if not video.name.endswith('/')
    ]

    videos.sort(
        key=lambda x: x.time_created,
        reverse=True
    )

    total_videos = len(videos)

    return render_template(
        'videos.html',
        videos=videos,
        bucket_name=BUCKET_NAME,
        total_videos=total_videos
    )




@app.route('/')
def index():
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # Grab all images
    image_blobs = list(bucket.list_blobs(prefix='images/'))
    image_blobs = [b for b in image_blobs if not b.name.endswith('/')]
    
    # Grab all videos
    video_blobs = list(bucket.list_blobs(prefix='videos/'))
    video_blobs = [b for b in video_blobs if not b.name.endswith('/')]
    
    # Combine them and sort by newest first
    all_media = image_blobs + video_blobs
    all_media.sort(key=lambda x: x.time_created, reverse=True)
    
    # Process the top 4 items
    recent_media = []
    for blob in all_media[:6]:
        filename = blob.name.split('/')[-1]
        is_video = blob.name.startswith('videos/')
        
        if is_video:
            recent_media.append({
                'type': 'video',
                'url': f"https://storage.googleapis.com/{BUCKET_NAME}/videos/{filename}"
            })
        else:
            recent_media.append({
                'type': 'image',
                'original': f"https://storage.googleapis.com/{BUCKET_NAME}/images/{filename}",
                'thumbnail': f"https://storage.googleapis.com/{BUCKET_NAME}/thumbnails/{filename}"
            })

    # Note: I changed the variable name from 'images' to 'media' here
    return render_template('index.html', media=recent_media)




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


# ----------_ADMIN ROUTES ----------

# ============================================================
# ADMIN LOGIN / PHOTO DASHBOARD
# ============================================================

@app.route('/admin', methods=['GET', 'POST'])
def admin():

    # --------------------------------------------------------
    # Admin password must be configured
    # --------------------------------------------------------

    if not ADMIN_PASSWORD:
        return "Admin password is not configured.", 500


    # --------------------------------------------------------
    # Handle login
    # --------------------------------------------------------

    if request.method == 'POST':

        password = request.form.get('password', '')


        if password == ADMIN_PASSWORD:

            session['is_admin'] = True

            return redirect(
                url_for('admin')
            )


        else:

            flash("Incorrect admin password.")

            return render_template(
                'admin.html',
                authenticated=False
            )


    # --------------------------------------------------------
    # If already logged in, show dashboard
    # --------------------------------------------------------

    if session.get('is_admin'):

        bucket = storage_client.bucket(
            BUCKET_NAME
        )


        # ====================================================
        # GET ALL IMAGES
        # ====================================================

        image_blobs = list(
            bucket.list_blobs(
                prefix='images/'
            )
        )


        image_blobs = [
            blob
            for blob in image_blobs
            if not blob.name.endswith('/')
        ]


        image_blobs.sort(
            key=lambda x: x.time_created,
            reverse=True
        )


        images = []


        for blob in image_blobs:

            filename = blob.name.split('/')[-1]


            images.append({

                'filename': filename,

                'original':
                    f"https://storage.googleapis.com/"
                    f"{BUCKET_NAME}/images/{filename}",

                'thumbnail':
                    f"https://storage.googleapis.com/"
                    f"{BUCKET_NAME}/thumbnails/{filename}"

            })


        return render_template(

            'admin.html',

            authenticated=True,

            images=images

        )


    # --------------------------------------------------------
    # Show login page
    # --------------------------------------------------------

    return render_template(

        'admin.html',

        authenticated=False

    )


# ============================================================
# ADMIN VIDEO MANAGEMENT
# ============================================================

@app.route('/admin/videos')
def admin_videos():

    # --------------------------------------------------------
    # Protect admin page
    # --------------------------------------------------------

    if not session.get('is_admin'):

        return redirect(
            url_for('admin')
        )


    bucket = storage_client.bucket(
        BUCKET_NAME
    )


    # --------------------------------------------------------
    # Get all videos
    # --------------------------------------------------------

    video_blobs = list(
        bucket.list_blobs(
            prefix='videos/'
        )
    )


    video_blobs = [

        blob

        for blob in video_blobs

        if not blob.name.endswith('/')

    ]


    video_blobs.sort(

        key=lambda x: x.time_created,

        reverse=True

    )


    videos = []


    for blob in video_blobs:

        filename = blob.name.split('/')[-1]


        videos.append({

            'filename': filename,

            'url':
                f"https://storage.googleapis.com/"
                f"{BUCKET_NAME}/videos/{filename}"

        })


    return render_template(

        'admin_videos.html',

        videos=videos

    )


# ============================================================
# DELETE IMAGE
# ============================================================

@app.route(
    '/admin/delete-image/<path:filename>',
    methods=['POST']
)
def delete_image(filename):

    # --------------------------------------------------------
    # Protect route
    # --------------------------------------------------------

    if not session.get('is_admin'):

        return redirect(
            url_for('admin')
        )


    bucket = storage_client.bucket(
        BUCKET_NAME
    )


    # --------------------------------------------------------
    # Delete original image
    # --------------------------------------------------------

    image_blob = bucket.blob(

        f"images/{filename}"

    )


    if image_blob.exists():

        image_blob.delete()


    # --------------------------------------------------------
    # Delete thumbnail too
    # --------------------------------------------------------

    thumbnail_blob = bucket.blob(

        f"thumbnails/{filename}"

    )


    if thumbnail_blob.exists():

        thumbnail_blob.delete()


    flash("Photo deleted successfully.")

    return redirect(

        url_for('admin')

    )


# ============================================================
# DELETE VIDEO
# ============================================================

@app.route(
    '/admin/delete-video/<path:filename>',
    methods=['POST']
)
def delete_video(filename):

    # --------------------------------------------------------
    # Protect route
    # --------------------------------------------------------

    if not session.get('is_admin'):

        return redirect(

            url_for('admin')

        )


    bucket = storage_client.bucket(

        BUCKET_NAME

    )


    video_blob = bucket.blob(

        f"videos/{filename}"

    )


    if video_blob.exists():

        video_blob.delete()


    flash("Video deleted successfully.")


    return redirect(

        url_for('admin_videos')

    )


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route('/admin/logout')
def admin_logout():

    session.pop(

        'is_admin',

        None

    )


    return redirect(

        url_for('admin')

    )

    



@app.errorhandler(413)
def request_entity_too_large(error):
    return 'Whoa, that file is massive! 🤯 Keep it under 500MB so we don\'t break the internet.', 413



if __name__ == '__main__':

    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(
        host="0.0.0.0",
        port=8080,
        debug=debug_mode
    )