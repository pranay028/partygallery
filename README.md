# Party Photos 📸

A private party media vault built with Flask and Google Cloud Storage.

> CODE GENERATED ENTIRELY WITH AI TOOLS (CHATGPT and GEMINI)

Users can:

- Upload multiple images
- Take photos directly from supported mobile devices
- Upload images later from their device
- Upload videos directly to Google Cloud Storage
- View recent photos and videos
- View all photos in a masonry-style camera roll
- See the current number of photos and videos
- Load photos progressively with pagination
- Open full-resolution images only when selected
- Automatically generate thumbnails for uploaded images
- Upload HEIC images
- Generate secure signed URLs for direct video uploads
- Automatically pause videos when they scroll out of view
- Use a password-protected admin panel
- Delete photos from the admin dashboard
- Delete videos from a separate admin video management page

---

# 🏗️ Project Architecture

```text
                         ┌───────────────────┐
                         │                   │
                         │     User          │
                         │     Browser       │
                         │                   │
                         └─────────┬─────────┘
                                   │
                                   ▼
                           ┌────────────────┐
                           │                │
                           │    Cloud Run   │
                           │    Flask App   │
                           │                │
                           └───────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
             Image Upload                  Signed Video URL
                    │                             │
                    ▼                             ▼
             Flask receives                Browser uploads
             image files                   directly to GCS
                    │                             │
                    ▼                             │
             Google Cloud Storage ◄───────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     images/   thumbnails/   videos/
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
    ├── videos.html
    ├── admin.html
    └── admin_videos.html
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

ADMIN_PASSWORD=replace-this-with-a-strong-admin-password

FLASK_DEBUG=true
```

Example:

```env
BUCKET_NAME=party28

APP_FLASK_SECRET_KEY=some-long-random-secret-key

ADMIN_PASSWORD=your-private-admin-password

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

The bucket should contain:

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

Google Cloud Storage creates object prefixes when files are uploaded.

---

### APP_FLASK_SECRET_KEY

Used by Flask for:

- Sessions
- Admin authentication sessions
- Flash messages

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

### ADMIN_PASSWORD

The password required to access:

```text
/admin
```

Example:

```env
ADMIN_PASSWORD=your-strong-password
```

The admin password should be configured as an environment variable.

For Cloud Run, configure it in the Cloud Run service environment variables or secrets configuration.

Do not hardcode it in:

- app.py
- HTML templates
- JavaScript
- GitHub repositories

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

The current project uses:

```text
partyphotos-501522
```

If you use a different project, update the relevant configuration.

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

The application uses:

```text
images/
thumbnails/
videos/
```

as object prefixes.

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

The application uses this service account for Google Cloud Storage access and signed URL generation.

---

# 🔑 7. Grant Storage Permissions

The service account needs permission to:

- Upload original images
- Upload thumbnails
- Read images
- Read thumbnails
- Read videos
- Delete objects through the admin panel
- Generate signed URLs

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

After the original image is uploaded, a background process creates a thumbnail.

The thumbnail is stored in:

```text
thumbnails/
```

Example:

```text
thumbnails/
└── uuid_originalfilename.jpg
```

The frontend initially displays thumbnails instead of full-resolution images.

This improves:

- Page loading speed
- Mobile performance
- Data usage
- Gallery scrolling performance

---

# 📸 12. Direct Camera Capture

The upload interface supports two main upload methods:

```text
Take Photo
     │
     ▼
Device Camera
     │
     ▼
Selected File
     │
     ▼
Upload
```

and:

```text
Choose Memories
     │
     ▼
Device File Picker
     │
     ▼
Selected Files
     │
     ▼
Upload
```

The camera input typically uses:

```html
<input
    type="file"
    accept="image/*"
    capture="environment"
>
```

Important:

- Camera support depends on the browser and device.
- The file must be attached to the upload input before submitting.
- iOS and Android may handle multiple file selection differently.
- Direct camera capture generally selects one image at a time.
- Users can still upload older photos through the normal file picker.

---

# 🍎 13. iOS Upload Considerations

iOS Safari can behave differently from Android browsers when selecting multiple files.

Recommended behavior:

- Use the normal file picker for multiple photos.
- Use the camera input for directly taking a new photo.
- Do not rely on the camera capture input for multiple image selection.

For multiple uploads:

```html
<input
    type="file"
    accept="image/*"
    multiple
>
```

For direct camera capture:

```html
<input
    type="file"
    accept="image/*"
    capture="environment"
>
```

These should be treated as separate upload experiences.

---

# 🖼️ 14. HEIC Support

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

The thumbnail can be converted to JPEG:

```python
img.save(
    thumb_io,
    format="JPEG",
    quality=80
)
```

The original HEIC file remains in Google Cloud Storage.

---

# 🎥 15. Video Upload Flow

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

- Flask does not need to process the entire video.
- Cloud Run receives less traffic.
- Large video uploads are faster.
- Memory usage is reduced.

---

# 🔗 16. Public Application Routes

## Home

```text
GET /
```

Displays:

- Upload interface
- Recent images
- Recent videos
- Image and video counts

---

## All Images

```text
GET /images
```

Displays the camera roll.

Features:

- Masonry-style layout
- Thumbnail-first loading
- Pagination
- Full-resolution image loading only when opened
- Current image count

Example:

```text
Camera Roll
124 PHOTOS
```

---

## Videos

```text
GET /videos
```

Displays uploaded videos.

Features:

- Video playback
- Video count
- Pagination
- Automatic pause when a video scrolls out of view

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

# 🎬 17. Automatic Video Pause

The videos page uses browser visibility detection.

When a video leaves the visible viewport:

```text
User watches video
        ↓
User scrolls down
        ↓
Video leaves screen
        ↓
Video automatically pauses
```

This prevents multiple videos from continuing to play while the user scrolls through the page.

This improves:

- Mobile battery usage
- Data usage
- User experience
- Audio control

A typical implementation uses:

```javascript
IntersectionObserver
```

to monitor video visibility.

---

# 🔐 18. Admin Panel

The admin panel is available at:

```text
/admin
```

The admin system uses:

```text
ADMIN_PASSWORD
```

and a Flask session.

The flow is:

```text
User
  │
  ▼
/admin
  │
  ▼
Enter password
  │
  ├── Incorrect
  │       │
  │       ▼
  │   Login error
  │
  └── Correct
          │
          ▼
    Admin session created
          │
          ▼
    Admin dashboard
```

After successful login:

```python
session["is_admin"] = True
```

The session is protected using:

```text
APP_FLASK_SECRET_KEY
```

---

# 🛠️ 19. Admin Dashboard

The admin dashboard is:

```text
/admin
```

After authentication, it displays:

- All uploaded images
- Image thumbnails
- Delete buttons
- Link to admin videos
- Logout button

The dashboard is intended to be the admin image management page.

The public navigation remains separate.

---

# 🗑️ 20. Delete Images

The image delete route should be protected by the admin session.

Example:

```text
POST /admin/delete-image/<filename>
```

The route should:

1. Check whether the user is authenticated.
2. Delete the original image.
3. Delete the corresponding thumbnail if it exists.
4. Redirect back to the admin dashboard.

The image deletion action should require confirmation in the browser:

```text
Delete this photo permanently?
```

Deletion is permanent unless Google Cloud Storage versioning is enabled.

---

# 🎬 21. Admin Videos

Admin video management is separate from the public videos page.

The admin video page is:

```text
/admin/videos
```

This page should display:

- Uploaded videos
- Video playback
- Delete buttons
- Admin navigation
- Logout button

The admin videos page must not redirect to:

```text
/videos
```

The public page:

```text
/videos
```

is for viewing videos.

The admin page:

```text
/admin/videos
```

is for managing and deleting videos.

---

# 🗑️ 22. Delete Videos

The video delete route should be protected by the admin session.

Example:

```text
POST /admin/delete-video/<filename>
```

The route should:

1. Check whether the user is authenticated.
2. Delete the video object from:

```text
videos/
```

3. Redirect back to:

```text
/admin/videos
```

The browser should ask for confirmation before deletion:

```text
Delete this video permanently?
```

---

# 🧭 23. Navigation

The public navigation contains:

```text
🏠 Home
📸 Photos
🎬 Videos
```

The public navigation links:

```text
/
 /images
 /videos
```

The admin management navigation should remain separate.

Recommended admin links:

```text
📸 Photos
🎬 Videos
🚪 Logout
```

Admin navigation:

```text
/admin
/admin/videos
```

Do not change the public Photos link to the admin page.

Public users should continue to access:

```text
/images
```

The admin should access:

```text
/admin
```

for image management.

---

# 🧪 24. Running Locally

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

Open:

```text
http://127.0.0.1:8080/admin
```

to test the admin panel.

---

# 🐛 25. Debug Mode

For local development:

```env
FLASK_DEBUG=true
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

# 🚀 26. Production Deployment Using Cloud Run

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

# 🐳 27. Dockerfile

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

# 🚫 28. .dockerignore

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

# ☁️ 29. Deploy to Cloud Run

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

Set the admin password:

```bash
gcloud run services update partyphotos \
    --region us-central1 \
    --set-env-vars ADMIN_PASSWORD="YOUR_ADMIN_PASSWORD"
```

> For a production application, Secret Manager is preferable to storing sensitive values directly as plain environment variables.

---

# 👤 30. Configure the Cloud Run Service Account

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

# 🔒 31. Important Security Rules

Never commit:

```text
.env
service-account.json
```

Never hardcode:

```python
APP_FLASK_SECRET_KEY
```

Never hardcode:

```python
ADMIN_PASSWORD
```

Never expose your service-account private key.

Never place your Google Cloud private key inside:

```text
templates/
static/
```

or any public directory.

The admin panel should always verify:

```python
session.get("is_admin")
```

before allowing deletion.

---

# 🛠️ 32. Common Problems

## Problem: Duplicate Flask Endpoint

Error:

```text
AssertionError:
View function mapping is overwriting an existing endpoint function
```

This means two routes are using the same endpoint function name.

For example:

```python
@app.route("/admin")
def admin():
    ...
```

and later:

```python
@app.route("/admin")
def admin():
    ...
```

Only define one function with the endpoint name:

```text
admin
```

Remove duplicate admin routes or rename the function.

---

## Problem: Admin Password Gives Internal Server Error

Check:

1. `ADMIN_PASSWORD` exists in Cloud Run.
2. The environment variable name is exactly:

```text
ADMIN_PASSWORD
```

3. `APP_FLASK_SECRET_KEY` is also configured.
4. The Cloud Run service account has required permissions.
5. The Cloud Run logs contain the actual traceback.

Check logs:

```bash
gcloud run services logs read partyphotos \
    --region us-central1
```

If the password is configured after deployment, make sure a new revision was created and traffic is directed to the latest revision.

---

## Problem: 404 Thumbnail

Example:

```text
No such object:
thumbnails/filename.jpg
```

This usually means:

- The original image exists.
- The thumbnail does not exist.
- Thumbnail generation failed.
- The image was uploaded before thumbnail generation was implemented.

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

if you want portrait and landscape proportions preserved.

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

The gallery should use:

```html
src="{{ img.thumbnail }}"
```

not:

```html
src="{{ img.original }}"
```

The full image should only be inserted when the modal opens.

This reduces initial data usage and improves gallery performance.

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
6. Cloud Run is running under the expected service account.

---

## Problem: Admin Delete Button Does Not Work

Check:

1. The user successfully logged in.
2. The session contains:

```python
session["is_admin"] = True
```

3. The delete route checks:

```python
if not session.get("is_admin"):
```

4. The route is using the correct storage object path.
5. The form action points to the admin delete route.

The public videos page should not be used for admin deletion.

Use:

```text
/admin/videos
```

for admin video management.

---

# 📊 33. Storage Layout

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
│   ├── uuid_photo2.jpg
│   └── uuid_photo3.jpg
│
└── videos/
    ├── uuid_video1.mp4
    └── uuid_video2.mov
```

---

# 💰 34. Google Cloud Costs

This project may incur costs for:

- Google Cloud Storage storage
- Storage operations
- Data transfer
- Cloud Run usage

For a small party application, usage may remain very low, but monitor your Google Cloud billing dashboard.

Consider setting up a billing budget alert.

---

# 🧹 35. Cleaning Up Old Files

List images:

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

# 🔄 36. Recommended Deployment Checklist

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
[ ] ADMIN_PASSWORD is configured
[ ] FLASK_DEBUG=false
[ ] Cloud Storage API is enabled
[ ] IAM Credentials API is enabled
[ ] Cloud Run service account has Storage permissions
[ ] Service account has Token Creator permissions
[ ] Bucket exists
[ ] Image uploads work
[ ] Direct camera capture works
[ ] Multiple image uploads work
[ ] Video uploads work
[ ] Signed URLs work
[ ] Thumbnail generation works
[ ] HEIC uploads work
[ ] Public image gallery works
[ ] Public video gallery works
[ ] Videos pause when scrolled off-screen
[ ] Admin login works
[ ] Admin image deletion works
[ ] Admin video deletion works
[ ] Admin logout works
```

---

# 🧪 37. Recommended Local Testing

## Image Upload

```text
[ ] JPG
[ ] PNG
[ ] HEIC
[ ] Portrait image
[ ] Landscape image
[ ] Multiple images
[ ] Direct camera photo
[ ] iPhone photo upload
[ ] Android photo upload
```

## Video Upload

```text
[ ] MP4
[ ] MOV
[ ] Large video
[ ] Video-only upload
```

## Gallery

```text
[ ] Thumbnail loads
[ ] Original does not load immediately
[ ] Full image opens when clicked
[ ] Portrait proportions are preserved
[ ] Landscape proportions are preserved
[ ] Load More works
[ ] Image count is displayed
[ ] Video count is displayed
[ ] Off-screen videos pause
```

## Admin

```text
[ ] /admin login works
[ ] Incorrect password is rejected
[ ] Correct password opens dashboard
[ ] Images are displayed
[ ] Images can be deleted
[ ] /admin/videos opens admin video page
[ ] Videos are displayed
[ ] Videos can be deleted
[ ] Logout works
[ ] Public /images remains public
[ ] Public /videos remains public
```

---

# 🏁 38. Final Production Architecture

```text
                         ┌───────────────────┐
                         │                   │
                         │     User          │
                         │     Browser       │
                         │                   │
                         └─────────┬─────────┘
                                   │
                                   ▼
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

- Flask
- Google Cloud Run
- Google Cloud Storage
- Signed URLs
- Pillow
- HEIC support
- Background thumbnail generation
- Responsive frontend layouts
- Mobile camera capture
- Progressive image loading
- Automatic video pausing
- Password-protected administration
- Admin photo deletion
- Admin video deletion

The most important production rules are:

> Keep large video uploads away from Flask whenever possible. Use signed URLs and upload directly to Google Cloud Storage.

> Keep admin credentials and Flask session secrets outside the source code.

> Keep public viewing routes separate from admin management routes.

This keeps the application faster, cheaper, safer, and easier to maintain.
