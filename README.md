# partygallery
# Party Photos 📸

A private party media vault built with Flask and Google Cloud Storage.

CODE GENERATED ENTIRELY WITH AI TOOLS (CHATGPT and GEMINI)


Users can:

* Upload multiple images
* Upload videos directly to Google Cloud Storage
* View recent photos and videos
* View all photos in a masonry-style camera roll
* Load photos progressively with pagination
* Open full-resolution images only when selected
* Automatically generate thumbnails for uploaded images
* Upload HEIC images
* Generate secure signed URLs for direct video uploads

---

## 🏗️ Project Architecture

```text
User Browser
     │
     │
     ├── Images
     │       │
     │       └── Flask /upload
     │                    │
     │                    ├── Original Image
     │                    │       ↓
     │                    │              Google Cloud Storage
     │                    │              images/
     │                    │
     │                    └── Background Thumbnail
     │                            ↓
     │                            Google Cloud Storage
     │                            thumbnails/
     │
     │
     └── Videos
             │
             ├── Flask generates Signed URL
             │
             └── Browser uploads directly to
                    Google Cloud Storage
                    videos/
```

---

# 📁 Project Structure

Recommended project structure:

```text
partyphotos/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── README.md
│
├── .env
│
├── service-account.json
│
└── templates/
    │
    ├── base.html
    ├── index.html
    ├── images.html
    └── videos.html
```

> Never commit `.env` or `service-account.json` to GitHub.

---

# 🐍 1. Python Requirements

This project requires Python 3.11+.

Python 3.13 should also work with the current dependencies.

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it on macOS/Linux:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 📦 2. requirements.txt

Create a file called:

```text
requirements.txt
```

Add:

```text
Flask
google-cloud-storage
google-auth
python-dotenv
Pillow
pillow-heif
gunicorn
```

Then install:

```bash
pip install -r requirements.txt
```

---

# 🔐 3. Environment Variables

Create a `.env` file in the root of the project:

```env
BUCKET_NAME=your-google-cloud-storage-bucket-name

APP_FLASK_SECRET_KEY=replace-this-with-a-long-random-secret-key

FLASK_DEBUG=true
```

Example:

```env
BUCKET_NAME=party28

APP_FLASK_SECRET_KEY=some-long-random-secret-key

FLASK_DEBUG=true
```

---

## Environment Variable Explanation

### BUCKET_NAME

The name of your Google Cloud Storage bucket.

Example:

```env
BUCKET_NAME=party28
```

This bucket should contain:

```text
party28/
│
├── images/
│
├── thumbnails/
│
└── videos/
```

The folders do not necessarily need to be manually created.

Google Cloud Storage creates them when files are uploaded.

---

### APP_FLASK_SECRET_KEY

Used by Flask for sessions and flash messages.

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Example:

```env
APP_FLASK_SECRET_KEY=8a9d4b...
```

Never commit this value to GitHub.

---

### FLASK_DEBUG

For local development:

```env
FLASK_DEBUG=true
```

For production:

```env
FLASK_DEBUG=false
```

Cloud Run should always run with:

```env
FLASK_DEBUG=false
```

---

# ☁️ 4. Google Cloud Project

Create or use a Google Cloud project.

The project ID used by this application is:

```text
partyphotos-501522
```

If you use a different project, update your configuration accordingly.

Enable the required APIs:

```bash
gcloud services enable storage.googleapis.com
```

Also enable:

```bash
gcloud services enable iamcredentials.googleapis.com
```

The IAM Credentials API is required for generating signed URLs using the Cloud Run service account.

---

# 🪣 5. Create a Google Cloud Storage Bucket

Create a bucket:

```bash
gcloud storage buckets create gs://YOUR_BUCKET_NAME \
    --location=us-central1
```

Example:

```bash
gcloud storage buckets create gs://party28 \
    --location=us-central1
```

Your bucket name must match:

```env
BUCKET_NAME=party28
```

---

# 👤 6. Create a Service Account

Create a service account for the application:

```bash
gcloud iam service-accounts create partyphotoslocal \
    --display-name="Party Photos Application"
```

This creates an email similar to:

```text
partyphotoslocal@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

The current project uses:

```text
partyphotoslocal@partyphotos-501522.iam.gserviceaccount.com
```

This value is used in:

```python
SERVICE_ACCOUNT_EMAIL = (
    "partyphotoslocal@partyphotos-501522.iam.gserviceaccount.com"
)
```

---

# 🔑 7. Grant Storage Permissions

The service account needs permission to:

* Upload original images
* Upload thumbnails
* Read images
* Read videos
* Generate signed URLs

Grant the Storage Object Admin role:

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectAdmin"
```

Example:

```bash
gcloud projects add-iam-policy-binding partyphotos-501522 \
    --member="serviceAccount:partyphotoslocal@partyphotos-501522.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

---

# 🔏 8. Allow the Service Account to Sign URLs

For signed video uploads, the service account needs permission to sign blobs.

Grant:

```bash
gcloud iam service-accounts add-iam-policy-binding \
    partyphotoslocal@partyphotos-501522.iam.gserviceaccount.com \
    --member="serviceAccount:partyphotoslocal@partyphotos-501522.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountTokenCreator"
```

This permission is important for:

```python
blob.generate_signed_url(
    version="v4",
    ...
)
```

---

# 💻 9. Local Development Credentials

For local development, create a service-account key.

Download the JSON credentials file from Google Cloud.

Save it locally as:

```text
service-account.json
```

Example:

```text
/Users/your-name/Desktop/partyphotos/service-account.json
```

Your local code can use:

```python
if not os.getenv("K_SERVICE"):
    os.environ[
        "GOOGLE_APPLICATION_CREDENTIALS"
    ] = "/Users/your-name/Desktop/partyphotos/service-account.json"
```

Important:

```text
service-account.json
```

must never be uploaded to GitHub.

---

# 🚫 10. .gitignore

Create:

```text
.gitignore
```

Add:

```text
venv/
.env
service-account.json
__pycache__/
*.pyc
.DS_Store
```

This protects your credentials.

---

# 🖼️ 11. Image Upload Flow

Images are uploaded to Flask:

```text
Browser
   ↓
POST /upload
   ↓
Flask
   ↓
Google Cloud Storage
   ↓
images/
```

The original image is stored in:

```text
images/
```

Example:

```text
images/
└── uuid_originalfilename.jpg
```

After the original image is uploaded, a background thread creates a thumbnail.

The thumbnail is stored in:

```text
thumbnails/
```

Example:

```text
thumbnails/
└── uuid_originalfilename.jpg
```

The thumbnail contains metadata:

```json
{
    "width": "4032",
    "height": "3024"
}
```

This allows the frontend to preserve portrait and landscape proportions.

---

# 🖼️ 12. HEIC Support

The application supports HEIC images using:

```python
import pillow_heif
```

and:

```python
pillow_heif.register_heif_opener()
```

This allows:

```python
Image.open(...)
```

to read HEIC images.

The thumbnail is converted to JPEG:

```python
img.save(
    thumb_io,
    format="JPEG",
    quality=80
)
```

The original HEIC file remains in Google Cloud Storage.

---

# 🎥 13. Video Upload Flow

Videos do not pass through Flask.

Instead:

```text
Browser
   │
   │ 1. Request signed URL
   ▼
Flask
   │
   │ 2. Generate temporary signed URL
   ▼
Browser
   │
   │ 3. Upload video directly
   ▼
Google Cloud Storage
```

The signed URL is temporary.

The current expiration time is:

```python
timedelta(minutes=15)
```

The video is stored in:

```text
videos/
```

Example:

```text
videos/
└── uuid_video.mp4
```

This is better than sending large videos through Flask because:

* Flask does not need to process the entire video
* Cloud Run receives less traffic
* Large video uploads are faster
* Memory usage is reduced

---

# 🔗 14. Application Routes

## Home

```text
GET /
```

Displays:

* Recent images
* Recent videos
* Upload interface

---

## All Images

```text
GET /images
```

Supports pagination:

```text
/images?page=1
/images?page=2
/images?page=3
```

The application currently loads:

```python
per_page = 20
```

photos per page.

The page initially loads thumbnails.

The full-resolution image is loaded only when the user opens the image modal.

---

## Videos

```text
GET /videos
```

Displays uploaded videos.

---

## Image Upload

```text
POST /upload
```

Receives image files.

The maximum request size is currently:

```python
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
```

This equals:

```text
500 MB
```

---

## Signed Video URL

```text
GET /get-signed-url
```

Example:

```text
/get-signed-url?filename=video.mp4&content_type=video/mp4
```

Returns:

```json
{
    "url": "temporary-signed-url"
}
```

---

# 🧪 15. Running Locally

Activate the virtual environment:

```bash
source venv/bin/activate
```

Make sure your `.env` exists.

Make sure your credentials exist:

```text
service-account.json
```

Run:

```bash
python app.py
```

The application runs at:

```text
http://localhost:8080
```

or:

```text
http://127.0.0.1:8080
```

---

# 🐛 16. Debug Mode

For local development:

```env
FLASK_DEBUG=true
```

The application contains:

```python
debug_mode = os.getenv(
    "FLASK_DEBUG",
    "false"
).lower() == "true"
```

Then:

```python
app.run(
    host="0.0.0.0",
    port=8080,
    debug=debug_mode
)
```

For production:

```env
FLASK_DEBUG=false
```

Never run production applications with:

```python
debug=True
```

---

# 🚀 17. Production Deployment Using Cloud Run

Cloud Run automatically provides credentials to the application.

Therefore, you should not upload:

```text
service-account.json
```

to Cloud Run.

The application detects Cloud Run using:

```python
if not os.getenv("K_SERVICE"):
```

Locally:

```text
GOOGLE_APPLICATION_CREDENTIALS
```

is used.

On Cloud Run:

```text
Application Default Credentials
```

are used automatically.

---

# 🐳 18. Dockerfile

Create:

```text
Dockerfile
```

with:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y \
        libheif1 \
        libheif-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

CMD exec gunicorn \
    --bind :$PORT \
    --workers 1 \
    --threads 8 \
    --timeout 0 \
    app:app
```

---

# 🚫 19. .dockerignore

Create:

```text
.dockerignore
```

Add:

```text
venv/
.env
service-account.json
.git/
__pycache__/
*.pyc
.DS_Store
```

---

# ☁️ 20. Deploy to Cloud Run

Build and deploy:

```bash
gcloud run deploy partyphotos \
    --source . \
    --region us-central1 \
    --allow-unauthenticated
```

Set the environment variables:

```bash
gcloud run services update partyphotos \
    --region us-central1 \
    --set-env-vars BUCKET_NAME=party28,FLASK_DEBUG=false
```

Set the Flask secret:

```bash
gcloud run services update partyphotos \
    --region us-central1 \
    --set-env-vars APP_FLASK_SECRET_KEY="YOUR_SECRET_KEY"
```

---

# 👤 21. Configure the Cloud Run Service Account

The Cloud Run service should run as:

```text
partyphotoslocal@partyphotos-501522.iam.gserviceaccount.com
```

Deploy using:

```bash
gcloud run deploy partyphotos \
    --source . \
    --region us-central1 \
    --service-account partyphotoslocal@partyphotos-501522.iam.gserviceaccount.com \
    --allow-unauthenticated
```

This allows the application to use:

```python
google.auth.default()
```

without a local JSON file.

---

# 🔒 22. Important Security Rules

Never commit:

```text
.env
service-account.json
```

Never hardcode:

```python
APP_FLASK_SECRET_KEY
```

Never expose your service-account private key.

Never place your Google Cloud private key inside:

```text
templates/
static/
```

or any public directory.

---

# 🛠️ 23. Common Problems

## Problem: 404 Thumbnail

Example:

```text
No such object:
thumbnails/filename.jpg
```

This usually means:

* The original image exists
* The thumbnail does not exist
* The thumbnail generation failed
* The image was uploaded before thumbnail generation was implemented

Possible solutions:

1. Delete old images and re-upload them.
2. Generate missing thumbnails.
3. Add a fallback to the original image.

The frontend can use:

```html
onerror="this.onerror=null; this.src='{{ img.original }}';"
```

---

## Problem: Images Are Square

Make sure your image uses:

```html
class="w-full h-auto block"
```

Do not use:

```html
class="aspect-square"
```

or:

```html
class="h-full object-cover"
```

if you want the original portrait and landscape proportions preserved.

For masonry layouts:

```html
<div class="columns-2 gap-3 space-y-3">

    <div class="break-inside-avoid">

        <img
            src="{{ img.thumbnail }}"
            class="w-full h-auto block"
        >

    </div>

</div>
```

---

## Problem: Full Images Load Too Early

The grid should use:

```html
src="{{ img.thumbnail }}"
```

not:

```html
src="{{ img.original }}"
```

The full image should only be inserted when the modal opens:

```javascript
function openImageModal(imgUrl) {

    content.innerHTML = `
        <img src="${imgUrl}">
    `;

}
```

---

## Problem: Upload Overlay Does Not Appear

Make sure the overlay is added before any `await`:

```javascript
document.body.appendChild(overlay);
```

Then begin the upload:

```javascript
await fetch(...)
```

If the form is submitted normally:

```javascript
form.submit();
```

the browser navigates to a new page, which is expected.

The overlay will disappear when the new page loads.

---

## Problem: Signed URL Error

Check:

1. The service account exists.
2. The service account has Storage permissions.
3. The IAM Credentials API is enabled.
4. The service account has:

```text
roles/iam.serviceAccountTokenCreator
```

5. The service account email is correct.

---

# 📊 24. Storage Layout

The bucket should eventually look like:

```text
party28/
│
├── images/
│   ├── uuid_photo1.jpg
│   ├── uuid_photo2.heic
│   └── uuid_photo3.png
│
├── thumbnails/
│   ├── uuid_photo1.jpg
│   ├── uuid_photo2.heic
│   └── uuid_photo3.png
│
└── videos/
    ├── uuid_video1.mp4
    └── uuid_video2.mov
```

---

# 💰 25. Google Cloud Costs

This project may incur costs for:

* Google Cloud Storage storage
* Storage operations
* Data transfer
* Cloud Run usage

For a small party application, usage may remain very low, but monitor your Google Cloud billing dashboard.

Consider setting up a billing budget alert.

---

# 🧹 26. Cleaning Up Old Files

You can list files:

```bash
gcloud storage ls gs://YOUR_BUCKET_NAME/images/
```

List thumbnails:

```bash
gcloud storage ls gs://YOUR_BUCKET_NAME/thumbnails/
```

List videos:

```bash
gcloud storage ls gs://YOUR_BUCKET_NAME/videos/
```

Delete a file:

```bash
gcloud storage rm gs://YOUR_BUCKET_NAME/images/FILENAME
```

Be careful when deleting files because Google Cloud Storage deletion is permanent unless versioning is enabled.

---

# 🔄 27. Recommended Deployment Checklist

Before deploying:

```text
[ ] requirements.txt exists
[ ] Dockerfile exists
[ ] .dockerignore exists
[ ] .gitignore exists
[ ] .env is not committed
[ ] service-account.json is not committed
[ ] BUCKET_NAME is correct
[ ] APP_FLASK_SECRET_KEY is configured
[ ] FLASK_DEBUG=false
[ ] Cloud Storage API is enabled
[ ] IAM Credentials API is enabled
[ ] Cloud Run service account has Storage permissions
[ ] Service account has Token Creator permissions
[ ] Bucket exists
[ ] Image uploads work
[ ] Video uploads work
[ ] Signed URLs work
[ ] Thumbnail generation works
[ ] HEIC uploads work
```

---

# 🧪 28. Recommended Local Testing

Test the following before deployment:

### Image Upload

```text
[ ] JPG
[ ] PNG
[ ] HEIC
[ ] Portrait image
[ ] Landscape image
[ ] Multiple images
```

### Video Upload

```text
[ ] MP4
[ ] MOV
[ ] Large video
[ ] Video-only upload
```

### Gallery

```text
[ ] Thumbnail loads
[ ] Original does not load immediately
[ ] Full image opens when clicked
[ ] Portrait proportions are preserved
[ ] Landscape proportions are preserved
[ ] Load More works
```

---

# 🏁 29. Final Production Architecture

The final production setup is:

```text
                         ┌───────────────────┐
                         │                   │
                         │     User          │
                         │     Browser       │
                         │                   │
                         └─────────┬─────────┘
                                   │
                                   │
                           ┌───────▼────────┐
                           │                 │
                           │    Cloud Run    │
                           │    Flask App    │
                           │                 │
                           └───────┬─────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    │                             │
            ┌───────▼────────┐           ┌────────▼────────┐
            │                 │           │                 │
            │  Google Cloud  │           │  Signed Video   │
            │  Storage       │           │  Upload URL     │
            │                 │           │                 │
            └───────┬─────────┘           └────────┬────────┘
                    │                              │
                    │                              │
        ┌───────────┼───────────┐                  │
        │           │           │                  │
        ▼           ▼           ▼                  ▼
    images/    thumbnails/   videos/       Browser → GCS
```

---

# 🎉 Done

The Party Photos application is designed to be a lightweight media-sharing application using:

* Flask
* Google Cloud Run
* Google Cloud Storage
* Signed URLs
* Pillow
* HEIC support
* Background thumbnail generation
* Responsive frontend layouts

The most important production rule is:

> Keep large video uploads away from Flask whenever possible. Use signed URLs and upload directly to Google Cloud Storage.

This keeps the application faster, cheaper, and more scalable.
