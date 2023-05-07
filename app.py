
# from flask import Flask, jsonify, request
# import requests
# import base64
# import tempfile
# import os
# from pdf2image import convert_from_bytes
# from io import BytesIO
# from PIL import Image
# from flask_cors import CORS

# import subprocess
# import mimetypes


# app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
# app.config['CORS_ALLOW_ALL_ORIGINS'] = True
# PORT = 8000
# HOST = '0.0.0.0'

# @app.route('/')
# def hello_world():
#     return 'Hello, World!'


# @app.route('/convert')
# def convert():
#     document_url = request.args.get('url')
#     page_number = request.args.get('pages') or 1
#     page_number = int(page_number)
#     if not document_url:
#         return jsonify({'error': 'URL is required'})

#     try:
#         response = requests.get(document_url)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         return jsonify({'error': str(e)})

#     # Get the file type from the response headers
#     content_type = response.headers.get('content-type')
#     file_ext = mimetypes.guess_extension(content_type)
#     if not file_ext:
#         return jsonify({'error': 'Unknown file type'})

#     # Use unoconv to convert the file to images
#     with tempfile.TemporaryDirectory() as temp_dir:
#         images = []
#         input_file = None
#         output_file = None
#         if file_ext == '.pdf':
#             pages = convert_from_bytes(response.content, output_folder=temp_dir)
#             for page in pages:
#                 img_buffer = BytesIO()
#                 page.save(img_buffer, format='PNG')
#                 img_buffer.seek(0)
#                 img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
#                 images.append(img_data)
#         else:
#             # Use unoconv to convert the file to PDF
#             input_file = os.path.join(temp_dir, 'input' + file_ext)
#             output_file = os.path.join(temp_dir, 'output.pdf')
#             with open(input_file, 'wb') as f:
#                 f.write(response.content)
#             subprocess.run(['unoconv', '-f', 'pdf', '-o', temp_dir, input_file], check=True)

#             # Convert the PDF to images
#             pages = convert_from_path(output_file, output_folder=temp_dir)
#             for page in pages:
#                 img_buffer = BytesIO()
#                 page.save(img_buffer, format='PNG')
#                 img_buffer.seek(0)
#                 img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
#                 images.append(img_data)

#         # Remove input and output files from the temp directory
#         if input_file:
#           os.remove(input_file)
#         if output_file:
#           os.remove(output_file)
#         # Remove images from the output directory
#         for filename in os.listdir(temp_dir):
#             file_path = os.path.join(temp_dir, filename)
#             try:
#                 if os.path.isfile(file_path):
#                     os.unlink(file_path)
#             except Exception as e:
#                 print(f'Error deleting {file_path}: {e}')
#     print('success',len(images))
#     return jsonify({'images': images[:page_number]})

# if __name__ == '__main__':
#     app.run(host=HOST, port=PORT, debug=True)



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

DPI = 300


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.config['CORS_ALLOW_ALL_ORIGINS'] = True
PORT = 8000
HOST = '0.0.0.0'


import math
import sys
import fitz

def split_pdf(input_file, temp_dir, chunk_size=10):
    # Check if the input file exists and has a non-zero size
    if not os.path.isfile(input_file) or os.path.getsize(input_file) == 0:
        sys.exit('Error: invalid PDF file')
    
    # Open the input PDF file
    with fitz.open(input_file) as doc:
        # Split the PDF file into chunks
        num_pages = doc.page_count
        chunks = []
        for i in range(0, num_pages, chunk_size):
            chunk_start = i
            chunk_end = min(i + chunk_size, num_pages)
            chunk_output = os.path.join(temp_dir, f'chunk_{chunk_start}_{chunk_end}.pdf')
            doc.select(range(chunk_start, chunk_end))
            doc.save(chunk_output)
            chunks.append(chunk_output)

    return chunks



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
            content_length = int(response.headers.get('content-length', 0))
            if content_length > CHUNK_SIZE:
                with tempfile.TemporaryDirectory() as temp_dir:
                  doc = fitz.open(input_file)
                  pages = min(page_number, doc.page_count)
                  for i in range(pages):
                      page = doc[i]
                      pix = page.get_pixmap()
                      img_buffer = BytesIO()
                      pix.save(img_buffer)
                      img_buffer.seek(0)
                      img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
                      images.append(img_data)
                  doc.close()
            else:
                with fitz.open(input_file) as doc:
                    pages = doc.page_count
                    for i in range(min(page_number, pages)):
                        page = doc.load_page(i)
                        pix = page.get_pixmap(alpha=False)
                        img_buffer = BytesIO()
                        pix.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
                        images.append(img_data)
        else:
            return jsonify({'error': 'Unsupported file type'})

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        # Delete the temporary input file
        if input_file and os.path.exists(input_file):
            os.remove(input_file)

    print('success', len(images))
    return jsonify({'images': images[:page_number]})



@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)





