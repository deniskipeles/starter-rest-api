'''
from flask import Flask, request, Response
from io import BytesIO
import requests
from pdf2image import convert_from_bytes
from PIL import Image
import json

app = Flask(__name__)
PORT = 3000
HOST = '0.0.0.0'

pdf2image_options = {
    'dpi': 300,
    'output_folder': './images',
    #'save_format': 'png',
    'size': (1920, 1080),
}
#images = convert_from_bytes(pdf_content, size=(800, None), grayscale=True, dpi=300, save_format='png')
@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/convert')
def convert_pdf_to_images():
    document_url = request.args.get('url')

    response = requests.get(document_url)
    if response.status_code != 200:
        return Response('Error fetching PDF', status=400)

    images = []
    for page in convert_from_bytes(response.content, **pdf2image_options):
        resized_image = page.resize((800, int(800/page.size[0]*page.size[1])))
        buffer = BytesIO()
        resized_image.save(buffer, 'PNG')
        images.append(buffer.getvalue())

    response_data = {'images': images}
    return Response(json.dumps(response_data), mimetype='application/json')

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
'''
from flask import Flask, jsonify, request
import requests
import base64
import tempfile
import os
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image

app = Flask(__name__)
PORT = 3000
HOST = '0.0.0.0'

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/convert')
def convert():
    document_url = request.args.get('url')
    if not document_url:
        return jsonify({'error': 'URL is required'})

    try:
        response = requests.get(document_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)})

    with tempfile.TemporaryDirectory() as temp_dir:
        images = []
        pages = convert_from_bytes(response.content, output_folder=temp_dir)
        for page in pages:
            img_buffer = BytesIO()
            page.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
            images.append(img_data)

    return jsonify({'images': images})

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)