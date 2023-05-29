# Use an official Python runtime as a parent image
FROM python:3.9-alpine

# Set the working directory to /app
WORKDIR /app

# Install system-level dependencies including curl and rustup
RUN apk update && apk add --no-cache curl && \
    apk add --no-cache --virtual .build-deps openssl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain stable && \
    export PATH="$HOME/.cargo/bin:$PATH" && \
    source $HOME/.cargo/env && \
    rustup default stable && \
    apk del .build-deps
    
    
    

# Install system-level dependencies
RUN apk update && apk add --no-cache gcc musl-dev libffi-dev openssl-dev \
    jpeg-dev zlib-dev libjpeg poppler-utils \
    gcc g++ cmake make mupdf-dev freetype-dev \
    wget

# ARG MUPDF=1.18.0
# RUN ln -s /usr/include/freetype2/ft2build.h /usr/include/ft2build.h \
#     && ln -s /usr/include/freetype2/freetype/ /usr/include/freetype \
#     && wget -c -q https://www.mupdf.com/downloads/archive/mupdf-${MUPDF}-source.tar.gz \
#     && tar xf mupdf-${MUPDF}-source.tar.gz \
#     && cd mupdf-${MUPDF}-source \
#     && make HAVE_X11=no HAVE_GLUT=no shared=yes prefix=/usr/local install \
#     && cd .. \
#     && rm -rf *.tar.gz mupdf-${MUPDF}-source

# Upgrade pip
RUN python -m pip install --upgrade pip
# RUN pip install PyMuPDF==1.22.2

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy and its language model
# RUN pip install transformers
# RUN pip install torch


# Install Pillow
RUN pip install --upgrade Pillow

# Install Flask-CORS
RUN pip install flask-cors

# Copy the application code into the container at /app
COPY . .

# Create the images directory
RUN mkdir images

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
