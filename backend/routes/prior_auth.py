from flask import Blueprint, request, jsonify
from agents.prior_auth_agent import run_prior_auth_agent

prior_auth_bp = Blueprint('prior_auth', __name__)

@prior_auth_bp.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request data is required"}), 400
    
    result = run_prior_auth_agent(data)
    return jsonify(result)

@prior_auth_bp.route('/sample', methods=['GET'])
def sample():
    return jsonify({
        "member_id": "MBR-20241234",
        "member_name": "John D.",
        "date_of_birth": "1952-03-15",
        "insurance_plan": "BlueCross PPO Gold",
        "requesting_provider": "Dr. Sarah Martinez, MD - Orthopedic Surgery",
        "npi": "1234567890",
        "procedure_code": "27447",
        "procedure_description": "Total Knee Arthroplasty, Right",
        "diagnosis_codes": ["M17.11", "E11.40", "Z68.33"],
        "clinical_justification": "Patient has failed 6 months of conservative treatment including physical therapy (24 sessions), NSAIDs, and corticosteroid injections. X-ray shows bone-on-bone arthritis. Functional impairment limits ADLs.",
        "requested_facility": "Regional Medical Center",
        "requested_date": "2025-02-15"
    })
