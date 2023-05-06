
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


def split_pdf1(input_file, temp_dir, chunk_size=10):
    # Open the input PDF file
    with open(input_file, 'rb') as f:
        input_pdf = PdfFileReader(f)

        # Split the PDF file into chunks
        num_pages = input_pdf.getNumPages()
        chunks = []
        for i in range(0, num_pages, chunk_size):
            chunk_start = i
            chunk_end = min(i + chunk_size, num_pages)
            chunk_output = os.path.join(temp_dir, f'chunk_{chunk_start}_{chunk_end}.pdf')
            with open(chunk_output, 'wb') as chunk_file:
                output_pdf = PdfFileWriter()
                for page in range(chunk_start, chunk_end):
                    output_pdf.addPage(input_pdf.getPage(page))
                output_pdf.write(chunk_file)
            chunks.append(chunk_output)

    return chunks


import math
import fitz

def split_pdf(input_file, temp_dir, chunk_size=10):
    # Create a temporary directory to store the chunked files
    os.makedirs(temp_dir, exist_ok=True)

    # Open the input PDF file
    with fitz.open(input_file) as doc:
        # Get the total number of pages
        num_pages = doc.page_count

        # Split the PDF file into chunks
        chunks = []
        for i in range(0, num_pages, chunk_size):
            chunk_start = i
            chunk_end = min(i + chunk_size, num_pages)
            chunk_output = os.path.join(temp_dir, f'chunk_{chunk_start}_{chunk_end}.pdf')
            with fitz.open() as chunk_doc:
                for page in range(chunk_start, chunk_end):
                    chunk_doc.insert_pdf(doc, from_page=page, to_page=page)
                chunk_doc.save(chunk_output)
            chunks.append(chunk_output)

    return chunks



CHUNK_SIZE = 5
OUTPUT_FORMAT = "png"

@app.route('/convert')
def convert():
    document_url = request.args.get('url')
    page_number = request.args.get('pages') or 1
    page_number = int(page_number)
    if not document_url:
        return jsonify({'error': 'URL is required'})

    try:
        response = requests.get(document_url, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)})

    # Get the file type from the response headers
    content_type = response.headers.get('content-type')
    file_ext = mimetypes.guess_extension(content_type)
    if not file_ext:
        return jsonify({'error': 'Unknown file type'})

    # Use unoconv to convert the file to images
    with tempfile.TemporaryDirectory() as temp_dir:
        images = []
        input_file = None
        output_file = None
        if file_ext == '.pdf':
            # Check the file size, and split it into chunks if necessary
            content_length = int(response.headers.get('content-length', 0))
            if content_length > CHUNK_SIZE:
                chunk_files = split_pdf(response.content, temp_dir, CHUNK_SIZE)
                for chunk_file in chunk_files:
                    pages = convert_from_path(chunk_file, dpi=DPI, output_folder=temp_dir, fmt=OUTPUT_FORMAT)
                    for page in pages:
                        img_buffer = BytesIO()
                        page.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
                        images.append(img_data)
            else:
                pages = convert_from_bytes(response.content, dpi=DPI, output_folder=temp_dir, fmt=OUTPUT_FORMAT)
                for page in pages:
                    img_buffer = BytesIO()
                    page.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
                    images.append(img_data)
        else:
            # Use unoconv to convert the file to PDF
            input_file = os.path.join(temp_dir, 'input' + file_ext)
            output_file = os.path.join(temp_dir, 'output.pdf')
            with open(input_file, 'wb') as f:
                f.write(response.content)
            subprocess.run(['unoconv', '-f', 'pdf', '-o', temp_dir, input_file], check=True)

            # Check the file size, and split it into chunks if necessary
            content_length = os.path.getsize(output_file)
            if content_length > CHUNK_SIZE:
                chunk_files = split_pdf(open(output_file, 'rb'), temp_dir, CHUNK_SIZE)
                for chunk_file in chunk_files:
                    pages = convert_from_path(chunk_file, dpi=DPI, output_folder=temp_dir, fmt=OUTPUT_FORMAT)
                    for page in pages:
                        img_buffer = BytesIO()
                        page.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
                        images.append(img_data)
            else:
                pages = convert_from_path(output_file, dpi=DPI, output_folder=temp_dir, fmt=OUTPUT_FORMAT)
                for page in pages:
                    img_buffer = BytesIO()
                    page.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
                    images.append(img_data)

        # Remove PDF chunks and input file from the temp directory
        for chunk_file in chunk_files:
            os.remove(chunk_file)
        if input_file:
            os.remove(input_file)
        if output_file:
            os.remove(output_file)

        # Remove images from the output directory
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Error deleting {file_path}: {e}')

    print('success',len(images))
    return jsonify({'images': images[:page_number]})




@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)





