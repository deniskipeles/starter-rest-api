# Use an official Python runtime as a parent image
FROM python:3.9-alpine

# Set the working directory to /app
WORKDIR /app

# Upgrade pip
#RUN pip install --upgrade pip
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade Pillow
RUN pip install flask-cors
RUN apk --no-cache add bash mc \
            curl \
            util-linux \
            libreoffice-common \
            libreoffice-writer \
            ttf-droid-nonlatin \
            ttf-droid \
            ttf-dejavu \
            ttf-freefont \
            ttf-liberation \
        && curl -Ls $UNO_URL -o /usr/local/bin/unoconv \
        && chmod +x /usr/local/bin/unoconv \
        && ln -s /usr/bin/python3 /usr/bin/python \
        && chmod +x convert.sh \
        && chmod +x timer.sh \
        && apk del curl \
        && rm -rf /var/cache/apk/*

RUN apk add gcc g++ cmake make mupdf-dev freetype-dev
ARG MUPDF=1.18.0
RUN ln -s /usr/include/freetype2/ft2build.h /usr/include/ft2build.h \
    && ln -s /usr/include/freetype2/freetype/ /usr/include/freetype \
    && wget -c -q https://www.mupdf.com/downloads/archive/mupdf-${MUPDF}-source.tar.gz \
    && tar xf mupdf-${MUPDF}-source.tar.gz \
    && cd mupdf-${MUPDF}-source \
    && make HAVE_X11=no HAVE_GLUT=no shared=yes prefix=/usr/local install \
    && cd .. \
    && rm -rf *.tar.gz mupdf-${MUPDF}-source
RUN pip install PyMuPDF==1.22.2

# Copy the requirements file into the container at /app
COPY requirements.txt .

RUN apk update

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

#RUN apk add --no-cache libreoffice unoconv

# Install poppler-utils
RUN apk add --no-cache poppler-utils

# Install system-level dependencies for Pillow
RUN apk add --no-cache jpeg-dev zlib-dev libjpeg

RUN mkdir images # Create the images directory
# Copy the rest of the application code into the container at /app
COPY . .

# Make port 3000 available to the world outside this container
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
