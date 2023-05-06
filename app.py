
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
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image
from flask_cors import CORS
import mimetypes
import subprocess
import multiprocessing

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.config['CORS_ALLOW_ALL_ORIGINS'] = True
PORT = 8000
HOST = '0.0.0.0'

def convert_to_images(content, temp_dir):
    images = []
    pages = convert_from_bytes(content, output_folder=temp_dir, dpi=150, fmt='png')
    for page in pages:
        img_buffer = BytesIO()
        page.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
        images.append(img_data)
    return images

@app.route('/')
def hello_world():
    return 'Hello, World!'


from multiprocessing import Pool

def convert_to_images(data, temp_dir):
    images = []
    pages = convert_from_bytes(data, dpi=300, output_folder=temp_dir, fmt='jpeg')
    for page in pages:
        img_buffer = BytesIO()
        page.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
        images.append(img_data)
    return images

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

    # Use multiprocessing to convert the file to images
    with tempfile.TemporaryDirectory() as temp_dir, Pool() as pool:
        images = []
        if file_ext == '.pdf':
            args = [(chunk, temp_dir) for chunk in response.iter_content()]
            results = pool.starmap(convert_to_images, args)
            for result in results:
                images += result
        else:
            # Convert the file to PDF using unoconv
            input_file = os.path.join(temp_dir, 'input' + file_ext)
            output_file = os.path.join(temp_dir, 'output.pdf')
            with open(input_file, 'wb') as f:
                for chunk in response.iter_content():
                    f.write(chunk)
            subprocess.run(['unoconv', '-f', 'pdf', '-o', temp_dir, input_file], check=True)

            # Convert the PDF to images
            pages = convert_from_path(output_file, dpi=300, output_folder=temp_dir, fmt='jpeg')
            for page in pages:
                img_buffer = BytesIO()
                page.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
                images.append(img_data)

            # Remove the input and output files
            os.remove(input_file)
            os.remove(output_file)

        # Remove images from the output directory
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Error deleting {file_path}: {e}')

    print('success', len(images))
    return jsonify({'images': images[:page_number]})



if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)





