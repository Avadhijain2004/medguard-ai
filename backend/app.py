from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

# Serve the frontend folder as static files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

from routes.medical_coding import medical_coding_bp
from routes.prior_auth import prior_auth_bp
from routes.claims import claims_bp
from routes.audit import audit_bp
from routes.device_form import device_form_bp

app.register_blueprint(medical_coding_bp, url_prefix='/api/medical-coding')
app.register_blueprint(prior_auth_bp, url_prefix='/api/prior-auth')
app.register_blueprint(claims_bp, url_prefix='/api/claims')
app.register_blueprint(audit_bp, url_prefix='/api/audit')
app.register_blueprint(device_form_bp, url_prefix='/api/device-form')

@app.route('/api/health')
def health():
    return {'status': 'ok', 'service': 'MedGuard AI Platform'}

# Serve frontend index at root
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# Serve any frontend page (e.g. /pages/medical-coding.html)
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)