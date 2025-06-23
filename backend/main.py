from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from resume_parser import extract_text_from_pdf
from classifier import classify_resume
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/classify', methods=['POST'])
def classify():
    file = request.files.get('resume')
    if not file or not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Please upload a valid PDF file."}), 400

    upload_folder = '../data'
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, file.filename)
    file.save(filepath)

    try:
        text = extract_text_from_pdf(filepath)
        category = classify_resume(text)
        return jsonify({"category": category})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)