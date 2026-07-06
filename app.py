import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from google.cloud import storage

# Load variables from .env file
load_dotenv()

app = Flask(__name__)

# Access the variables
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Initialize client with the project ID
storage_client = storage.Client(project=PROJECT_ID)
# Helper to route files
def get_folder(filename):
    ext = filename.lower().split('.')[-1]
    if ext in ['mp4', 'mov', 'avi', 'mkv']:
        return 'videos/'
    return 'images/'

@app.route('/images')
def images():
    bucket = storage_client.bucket(BUCKET_NAME)
    # 1. Fetch only files in the 'images/' folder
    blobs = list(bucket.list_blobs(prefix='images/'))
    
    # 2. Sort by 'time_created', reverse=True means newest first
    blobs.sort(key=lambda x: x.time_created, reverse=True)
    
    # 3. Create the direct public URLs
    image_urls = [f"https://storage.googleapis.com/{BUCKET_NAME}/{blob.name}" for blob in blobs]
    
    return render_template('images.html', images=image_urls)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and file.filename:
        # Save to 'images/' folder in bucket
        blob = storage_client.bucket(BUCKET_NAME).blob('images/' + file.filename)
        blob.upload_from_file(file, content_type=file.content_type)
    return redirect(url_for('index'))

@app.route('/videos')
def videos():
    # Only fetch from the videos folder
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix='videos/')
    return render_template('videos.html', videos=blobs)

@app.route('/')
def index():
    bucket = storage_client.bucket(BUCKET_NAME)
    # Fetch blobs from images/
    blobs = list(bucket.list_blobs(prefix='images/'))
    
    # Sort by time created, reverse=True means the newest items come first
    blobs.sort(key=lambda x: x.time_created, reverse=True)
    
    # Create the URLs
    image_urls = [f"https://storage.googleapis.com/{BUCKET_NAME}/{blob.name}" for blob in blobs]
    
    # Pass only the first 4 (or however many you want for "highlights") to the template
    return render_template('index.html', images=image_urls[:4])

if __name__ == '__main__':
    # '0.0.0.0' makes it accessible on your local network
    # 8080 is the default port Cloud Run expects
    # debug=True allows the server to auto-reload when you save your code
    app.run(host='0.0.0.0', port=8080, debug=True)