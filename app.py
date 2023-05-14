
from flask import Flask, jsonify, request
import requests
import base64
import tempfile
import os
from pdf2image import convert_from_bytes, convert_from_path
from io import BytesIO
from PIL import Image
from flask_cors import CORS
import mimetypes
import subprocess
from PyPDF2 import PdfFileReader

DPI = 150


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.config['CORS_ALLOW_ALL_ORIGINS'] = True
PORT = 8000
HOST = '0.0.0.0'


import math
import sys
import fitz
import subprocess

def convert_to_pdf(input_file):
    output_file = f"{os.path.splitext(input_file)[0]}.pdf"
    cmd = ["unoconv", "-f", "pdf", "-o", output_file, input_file]
    subprocess.run(cmd, check=True)
    return output_file



def get_file_extension(url):
    # Use mimetypes to get the MIME type of the file
    if url.__contains__('.docx'):
      return '.docx'
      
    content_type, _ = mimetypes.guess_type(url)
    # Try to guess the extension from the MIME type
    file_ext = mimetypes.guess_extension(content_type)
    # If guess_extension fails, try to get the extension from the URL
    if file_ext is None:
        file_ext = os.path.splitext(url)[1]
    return file_ext

CHUNK_SIZE = 3
OUTPUT_FORMAT = "png"

@app.route('/convert')
def convert():
    document_url = request.args.get('url')
    page_number = request.args.get('pages') or 1
    page_number = int(page_number)
    if not document_url:
        return jsonify({'error': 'URL is required'})
    # Get the file type from - response header
    response = None
    images = []
    input_file = None
    temp_image = None
    file_ext = get_file_extension(document_url)
    try:
        # Get the file type from the response headers
        response = requests.get(document_url, stream=True)
        if not file_ext:
            return jsonify({'error': 'Unknown file type'})
        if file_ext != '.pdf':
            return jsonify({'error': 'Unsupported file type'})
        # Download the document file to a temporary file
        if file_ext == '.pdf':
          with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
              response.raise_for_status()
              for chunk in response.iter_content(chunk_size=8192):
                  temp_file.write(chunk)
          input_file = temp_file.name

        # Check the file type and split the file into chunks if necessary
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpeg') as temp_image:
            doc = fitz.open(input_file)
            pages = min(page_number, doc.page_count)
            for i in range(pages):
                page = doc[i]
                pix = page.get_pixmap()
                pix.save(temp_image.name)
                with open(temp_image.name, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                    images.append(img_data)
            doc.close()

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        # Delete the temporary input and image files
        if input_file and os.path.exists(input_file):
            os.remove(input_file)
        if temp_image and os.path.exists(temp_image.name):
            os.remove(temp_image.name)

    return jsonify({'images': len(images)})

'''
@app.route('/convert')
def convert():
    document_url = request.args.get('url')
    page_number = request.args.get('pages') or 1
    page_number = int(page_number)
    if not document_url:
        return jsonify({'error': 'URL is required'})
    # Get the file type from - response header
    response = None
    images = []
    try:
        # Download the document file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            response = requests.get(document_url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
        input_file = temp_file.name

        # Check the file type and split the file into chunks if necessary
        file_ext = os.path.splitext(input_file)[1]
        if file_ext.lower() == '.pdf':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpeg') as temp_image:
                doc = fitz.open(input_file)
                pages = min(page_number, doc.page_count)
                for i in range(pages):
                    page = doc[i]
                    pix = page.get_pixmap()
                    pix.save(temp_image.name)
                    with open(temp_image.name, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                        images.append(img_data)
                doc.close()
        else:
            return jsonify({'error': 'Unsupported file type'})

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        # Delete the temporary input and image files
        if input_file and os.path.exists(input_file):
            os.remove(input_file)
        if temp_image and os.path.exists(temp_image.name):
            os.remove(temp_image.name)

    #print('success', len(images))
    return jsonify({'images': len(images)})
'''
@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)





