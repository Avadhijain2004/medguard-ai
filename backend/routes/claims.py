from flask import Blueprint, request, jsonify
from agents.claims_adjudication_agent import run_claims_adjudication_agent

claims_bp = Blueprint('claims', __name__)

@claims_bp.route('/adjudicate', methods=['POST'])
def adjudicate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Claim data is required"}), 400
    
    result = run_claims_adjudication_agent(data)
    return jsonify(result)

@claims_bp.route('/sample', methods=['GET'])
def sample():
    return jsonify({
        "claim_id": "CLM-2024-089234",
        "member_id": "MBR-20241234",
        "provider_npi": "1234567890",
        "provider_name": "Regional Medical Center",
        "service_date": "2025-01-20",
        "procedure_code": "27447",
        "diagnosis_code": "M17.11",
        "modifier": "RT",
        "place_of_service": "21",
        "billed_amount": 28500.00,
        "authorization_number": "AUTH-PRE2024123",
        "revenue_code": "0360",
        "units": 1
    })
