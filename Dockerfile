# Use official lightweight Python image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=True

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy local code to the container
COPY . .

# Run the web service using Gunicorn
# --limit-request-line 0 and --limit-request-field_size 0 are the keys
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 3600 \
    --limit-request-line 0 \
    --limit-request-field_size 0 \
    app:app