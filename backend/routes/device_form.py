from flask import Blueprint, request, jsonify
from agents.device_form_agent import run_device_form_agent

device_form_bp = Blueprint('device_form', __name__)

@device_form_bp.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Form data is required"}), 400
    
    result = run_device_form_agent(
        form_data=data,
        document_text=data.get('document_text', '')
    )
    return jsonify(result)

@device_form_bp.route('/sample', methods=['GET'])
def sample():
    return jsonify({
        "device_name": "Zimmer Biomet Persona Knee System",
        "manufacturer": "Zimmer Biomet",
        "udi_di": "00813263005043",
        "lot_number": "A123456",
        "serial_number": "SN-2024-78901",
        "expiration_date": "2027-12-31",
        "catalog_number": "PS-TC-7R",
        "implant_date": "2025-01-20",
        "patient_id": "PT-2024-5678",
        "surgeon": "Dr. Sarah Martinez, MD",
        "facility": "Regional Medical Center",
        "facility_id": "FAC-IL-0023",
        "implant_site": "Right Knee",
        "laterality": "Right",
        "procedure": "Total Knee Arthroplasty",
        "anesthesia_type": "Spinal"
    })
