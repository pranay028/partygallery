import os
import uuid
import threading
from dotenv import load_dotenv
from flask import Flask, render_template, flash, request, redirect, url_for
from google.cloud import storage
import datetime
from PIL import Image
import io
import pillow_heif
# This registers the HEIC format so Image.open() recognizes it
pillow_heif.register_heif_opener()

# Load variables from .env file
load_dotenv()

# Only load the local JSON file if we are NOT in production
# Cloud Run automatically sets the 'K_SERVICE' environment variable
if not os.getenv('K_SERVICE'):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/pranay/Desktop/partyphotos/service-account.json"

# Now initialize the client (this will work in both environments)
storage_client = storage.Client()

app = Flask(__name__)
app.secret_key = 'your_super_secret_random_string_here'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
# Access the variables
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Initialize client with the project ID
storage_client = storage.Client(project=PROJECT_ID)
# Helper to route files
def get_folder(filename):
    # Get the extension (e.g., 'mp4', 'jpg')
    ext = filename.lower().split('.')[-1]
    # Add video extensions here
    if ext in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
        return 'videos/'
    return 'images/'

def generate_thumbnail_in_background(file_bytes, unique_filename, bucket_name, project_id):
    try:
        # 1. Create a fresh connection for the background worker
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        
        # 2. Open the image from memory
        img = Image.open(io.BytesIO(file_bytes))
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img.thumbnail((400, 400))
        
        # 3. Save it and upload the thumbnail
        thumb_io = io.BytesIO()
        img.save(thumb_io, format='JPEG', quality=80)
        thumb_io.seek(0)
        
        thumb_blob = bucket.blob(f"thumbnails/{unique_filename}")
        thumb_blob.upload_from_file(thumb_io, content_type='image/jpeg')
        
    except Exception as e:
        print(f"DEBUG: Background thumbnail failed: {e}")

@app.route('/images')
def images():
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # Fetch blobs from images/
    all_blobs = list(bucket.list_blobs(prefix='images/'))
    file_blobs = [b for b in all_blobs if not b.name.endswith('/')]
    
    # Sort by time created, reverse=True means newest first
    file_blobs.sort(key=lambda x: x.time_created, reverse=True)
    
    images_data = []
    for blob in file_blobs:
        filename = blob.name.split('/')[-1] 
        images_data.append({
            'original': f"https://storage.googleapis.com/{BUCKET_NAME}/images/{filename}",
            'thumbnail': f"https://storage.googleapis.com/{BUCKET_NAME}/thumbnails/{filename}"
        })
    
    # Notice we don't slice with [:4] here, because we want ALL of them
    return render_template('images.html', images=images_data)

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    bucket = storage_client.bucket(BUCKET_NAME)
    
    for file in files:
        if not file or file.filename == '': continue
        
        # Now this route ONLY receives images from the frontend
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

# @app.route('/upload', methods=['POST'])
# def upload():
#     files = request.files.getlist('files')
#     print(f"DEBUG: Received {len(files)} files") # Check the logs for this!
#     if len(files) == 0:
#         return "No files received", 400
#     # ... rest of your code
#     # 1. Separate files by type
#     images = [f for f in files if f.filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'heic'}]
#     videos = [f for f in files if f.filename.rsplit('.', 1)[1].lower() in {'mp4', 'mov', 'avi', 'webm', 'mkv'}]
    
#     # 2. Enforce limits
#     if len(images) > 10:
#         flash("You can only upload up to 10 photos at a time.")
#         return redirect(url_for('index'))
        
#     if len(videos) > 1:
#         flash("You can only upload 1 video at a time.")
#         return redirect(url_for('index'))

#     bucket = storage_client.bucket(BUCKET_NAME)
    
#     # 3. Process files
#     for file in files:
#         if not file or file.filename == '': continue
            
#         ext = file.filename.rsplit('.', 1)[1].lower()
#         unique_filename = f"{uuid.uuid4()}_{file.filename}"
        
#         file.seek(0)
        
#         if ext in {'png', 'jpg', 'jpeg', 'gif', 'heic'}:
#             file_bytes = file.read()
#             blob = bucket.blob(f"images/{unique_filename}")
#             blob.upload_from_string(file_bytes, content_type=file.content_type)
            
#             thread = threading.Thread(
#                 target=generate_thumbnail_in_background, 
#                 args=(file_bytes, unique_filename, BUCKET_NAME, PROJECT_ID)
#             )
#             thread.start()
#             return redirect(url_for('index'))
                
#         elif ext in {'mp4', 'mov', 'avi', 'webm', 'mkv'}:
#             blob = bucket.blob(f"videos/{unique_filename}")
#             blob.upload_from_file(file, content_type=file.content_type)
#             return redirect(url_for('videos'))
#         else:
#             flash(f"Unsupported file type: {file.filename}")
            
#     return "Upload error please try again"
    

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
    
    # Create a list of dictionaries containing BOTH URLs
    images_data = []
    for blob in file_blobs:
        # Get just the filename (e.g., '1234_party.jpg')
        filename = blob.name.split('/')[-1] 
        
        images_data.append({
            'original': f"https://storage.googleapis.com/{BUCKET_NAME}/images/{filename}",
            'thumbnail': f"https://storage.googleapis.com/{BUCKET_NAME}/thumbnails/{filename}"
        })
    
    # Pass the dictionary to the template
    return render_template('index.html', images=images_data[:4])

@app.route('/get-signed-url', methods=['GET'])
def get_signed_url():
    filename = request.args.get('filename')
    folder = get_folder(filename)
    unique_name = f"{folder}{uuid.uuid4()}_{filename}"
    
    blob = storage_client.bucket(BUCKET_NAME).blob(unique_name)
    
    # Generate a URL that allows a PUT request for 15 minutes
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="PUT",
        content_type=request.args.get('content_type')
    )
    return {"url": url}



from werkzeug.exceptions import RequestEntityTooLarge

@app.errorhandler(413)
def request_entity_too_large(error):
    return 'File too large! Max is 100MB', 413

if __name__ == '__main__':
    # '0.0.0.0' makes it accessible on your local network
    # 8080 is the default port Cloud Run expects
    # debug=True allows the server to auto-reload when you save your code
    app.run(host='0.0.0.0', port=8080, debug=True)