# Use an official Python runtime as a parent image
FROM python:3.9-alpine

# Set the working directory to /app
WORKDIR /app

# Upgrade pip
#RUN pip install --upgrade pip
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade Pillow
# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# RUN apk add tiff-dev jpeg-dev openjpeg-dev zlib-dev freetype-dev lcms2-dev && \
#     libwebp-dev tcl-dev tk-dev harfbuzz-dev fribidi-dev libimagequant-dev && \
#     libxcb-dev libpng-dev
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# Install poppler-utils
RUN apk add --no-cache poppler-utils

# Install system-level dependencies for Pillow
RUN apk add --no-cache jpeg-dev zlib-dev libjpeg

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 3000 available to the world outside this container
EXPOSE 3000

CMD ["gunicorn", "--bind", "0.0.0.0:3000", "app:app"]
