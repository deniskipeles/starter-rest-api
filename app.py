
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
from flask import make_response
import io
# from PyPDF2 import PdfFileReader

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
import spacy





@app.route('/summary')
def summarize():
    text_file_url = request.args.get('url')
    text_string = request.args.get('txt')  # Get the txt query parameter

    if not text_file_url and not text_string:
        return jsonify({'error': 'Text file URL or txt parameter is required'})

    response = None
    text = None

    try:
        if text_string:
            # Use the provided text string
            text = text_string
        else:
            # Get the file type from the response headers
            response = requests.get(text_file_url, stream=True)
            response.raise_for_status()

            # Extract the text from the text file
            text = response.text

        # Perform text summarization using spaCy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        summary = " ".join(sentences[:5])  # Adjust the number of sentences as needed

        return jsonify({'summary': summary})

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        if response:
            response.close()

    # Handle the case where an exception is raised and no JSON response is returned
    return jsonify({'error': 'An unexpected error occurred'})






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

@app.route('/pdf/images')
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

@app.route('/')
def hello_world():
    return 'Hello, World!'




@app.route('/pdf/text')
def pdf_to_text():
    pdf_file_url = request.args.get('url')

    if pdf_file_url:
        try:
            # Download the PDF file
            response = requests.get(pdf_file_url)
            response.raise_for_status()

            # Load the PDF data using PyMuPDF
            pdf_data = response.content
            pdf = fitz.open(stream=pdf_data, filetype="pdf")

            # Extract text from each page
            extracted_text = ""
            for page in pdf:
                extracted_text += page.get_text()

            # Close the PDF
            pdf.close()

            # Create a buffer to hold the text content
            text_buffer = io.BytesIO()

            # Write the extracted text to the buffer
            text_buffer.write(extracted_text.encode('utf-8'))
            text_buffer.seek(0)  # Reset the buffer position

            # Create a Flask response with the text buffer as the content
            response = make_response(text_buffer.getvalue())

            # Set the appropriate headers for the response
            response.headers['Content-Disposition'] = 'attachment; filename=extracted_text.txt'
            response.headers['Content-Type'] = 'text/plain'

            return response

        except requests.exceptions.RequestException as e:
            return f"Error downloading the PDF: {str(e)}"

    return "No PDF URL provided."


@app.route('/pdf/html')
def pdf_to_html():
    pdf_file_url = request.args.get('url')

    if pdf_file_url:
        try:
            # Download the PDF file
            response = requests.get(pdf_file_url)
            response.raise_for_status()

            # Load the PDF data using PyMuPDF
            pdf_data = response.content
            pdf = fitz.open(stream=pdf_data, filetype="pdf")

            # Convert the first 10 pages to HTML
            html_pages = []
            num_pages = min(10, len(pdf))  # Limit the number of pages
            for page in range(num_pages):
                html = pdf[page].get_text("html")
                html_pages.append(html)

            # Close the PDF
            pdf.close()

            # Concatenate the HTML pages into a single HTML string
            html_content = "\n".join(html_pages)

            # Return the HTML content as a JSON response
            return jsonify(html=html_content)

        except requests.exceptions.RequestException as e:
            return jsonify(error=f"Error downloading the PDF: {str(e)}")

    return jsonify(error="No PDF URL provided.")


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)





