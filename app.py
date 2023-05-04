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
    'save_format': 'png',
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
