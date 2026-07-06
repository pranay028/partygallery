import os
from dotenv import load_dotenv
from flask import Flask
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

@app.route('/')
def index():
    # Fetch recent uploads from both to show highlights
    images = list(storage_client.list_blobs(BUCKET_NAME, prefix='images/'))[:4]
    return render_template('index.html', images=images)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        folder = get_folder(file.filename)
        blob = storage_client.bucket(BUCKET_NAME).blob(folder + file.filename)
        blob.upload_from_file(file, content_type=file.content_type)
    return redirect(url_for('index'))

@app.route('/videos')
def videos():
    # Only fetch from the videos folder
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix='videos/')
    return render_template('videos.html', videos=blobs)