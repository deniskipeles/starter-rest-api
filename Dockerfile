# Use an official Python runtime as a parent image
FROM python:3.9-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# Install poppler-utils
RUN apk add --no-cache poppler-utils

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Run the app using gunicorn when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "app:app"]
