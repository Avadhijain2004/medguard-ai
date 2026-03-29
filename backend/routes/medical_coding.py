from flask import Blueprint, request, jsonify
from agents.medical_coding_agent import run_medical_coding_agent

medical_coding_bp = Blueprint('medical_coding', __name__)

@medical_coding_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'clinical_note' not in data:
        return jsonify({"error": "clinical_note is required"}), 400
    
    result = run_medical_coding_agent(
        clinical_note=data['clinical_note'],
        patient_context=data.get('patient_context', {})
    )
    return jsonify(result)

@medical_coding_bp.route('/sample', methods=['GET'])
def sample():
    return jsonify({
        "clinical_note": """HISTORY: 72-year-old male with Type 2 diabetes mellitus with diabetic peripheral neuropathy presents for evaluation of severe right knee pain. Patient has a BMI of 32.4. X-ray demonstrates end-stage osteoarthritis of the right knee with bone-on-bone changes.

ASSESSMENT:
1. Severe osteoarthritis, right knee (primary)
2. Type 2 diabetes mellitus with diabetic peripheral neuropathy
3. Morbid obesity (BMI 32.4)

PLAN: Patient is a candidate for right total knee arthroplasty (TKA). Will proceed with surgical planning. Pre-operative cardiology clearance required given diabetes history.""",
        "patient_context": {"age": 72, "gender": "M", "insurance": "Medicare"}
    })
