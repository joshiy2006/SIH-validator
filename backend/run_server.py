import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

# This import connects the server to your OCR code
from verifier.ocr_logic import process_and_verify_image

# --- FLASK SERVER SETUP ---
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/verify', methods=['POST'])
def verify_certificate_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filepath = ""
        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Call the main function from your OCR script
            final_report = process_and_verify_image(filepath)
            
            return jsonify(final_report)

        except Exception as e:
            print(f"An error occurred: {e}")
            return jsonify({"isAuthentic": False, "confidence": 0, "overallStatus": "fraudulent", "error": str(e)}), 500
        finally:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)

# --- MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    print("="*50)
    print("DocuVerify Backend Server Starting...")
    print(f"API endpoint available at: http://127.0.0.1:5000/api/verify")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)