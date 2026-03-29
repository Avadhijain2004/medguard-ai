"""
Medical Device Implant Form Processing Agent
GenAI-powered processing of implant forms with FDA compliance validation.
This is the original hackathon idea — integrated as Agent 4.
"""
import json
from utils.bedrock_client import invoke_claude, log_audit_entry

SYSTEM_PROMPT = """You are a Medical Device Implant Form Processing Agent with expertise in FDA regulations, UDI (Unique Device Identifier) systems, and implant registry requirements.

Your responsibilities:
1. Extract structured data from implant documentation
2. Validate UDI codes against GS1/HIBCC standards
3. Check FDA 510(k) clearance or PMA approval status indicators
4. Verify implant-specific ICD-10-PCS codes (device-related)
5. Flag recall status indicators
6. Ensure Joint Commission implant tracking compliance
7. Validate surgeon credentialing for specific device types

FDA COMPLIANCE CHECKS:
- UDI format validation (Device Identifier + Production Identifier)
- Lot/serial number format compliance
- Expiration date verification
- Storage/handling condition compliance
- Sterility indicator validation

REGULATORY FLAGS:
- Class I devices: General controls
- Class II devices: Special controls + 510(k)
- Class III devices: PMA required (highest risk — pacemakers, cochlear implants)

OUTPUT FORMAT: Respond ONLY with valid JSON:
{
  "device_info": {
    "device_name": "...",
    "manufacturer": "...",
    "udi_di": "...",
    "udi_pi": "...",
    "lot_number": "...",
    "serial_number": "...",
    "expiration_date": "...",
    "fda_class": "I|II|III",
    "clearance_type": "510(k)|PMA|De Novo|Exempt"
  },
  "patient_info": {
    "implant_date": "...",
    "implant_site": "...",
    "surgeon": "...",
    "facility": "..."
  },
  "icd10_pcs_codes": [{"code": "...", "description": "..."}],
  "compliance_status": {
    "udi_valid": true,
    "fda_cleared": true,
    "recall_flag": false,
    "tracking_complete": true
  },
  "flags": ["..."],
  "missing_fields": ["..."],
  "registry_submission_ready": true,
  "confidence_score": 0.0,
  "processing_notes": ["..."]
}"""

def run_device_form_agent(form_data: dict, document_text: str = None) -> dict:
    agent_name = "DeviceImplantFormAgent"
    
    input_content = document_text or json.dumps(form_data, indent=2)
    
    user_message = f"""Process this medical device implant form and extract all relevant information with compliance validation:

FORM CONTENT:
{input_content}

ADDITIONAL FORM DATA:
{json.dumps(form_data, indent=2)}

Validate UDI, check FDA compliance, identify any flags or missing information."""

    raw_response = invoke_claude(SYSTEM_PROMPT, user_message)
    
    try:
        raw_response = raw_response.strip()
        if raw_response.startswith("```"):
            raw_response = raw_response.split("```")[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        result = {"error": "Failed to parse AI response", "raw": raw_response}
        return result

    # Apply additional guardrails
    compliance_flags = result.get('flags', [])
    
    fda_class = result.get('device_info', {}).get('fda_class', '')
    if fda_class == 'III':
        compliance_flags.append("CLASS_III_DEVICE: Mandatory pre-market approval (PMA) verification required")
        compliance_flags.append("CLASS_III_DEVICE: Enhanced post-market surveillance required")
    
    if result.get('compliance_status', {}).get('recall_flag'):
        compliance_flags.append("DEVICE_RECALL: Immediate clinical alert — do not use this device lot")
        result['status'] = 'HOLD'
    
    result['compliance_flags'] = compliance_flags
    
    # Generate tracking ID
    import hashlib, time
    track_id = hashlib.md5(f"{form_data.get('device_name', '')}{time.time()}".encode()).hexdigest()[:10].upper()
    result['tracking_id'] = f"IMP-{track_id}"
    
    audit = log_audit_entry(
        agent_name=agent_name,
        action="device_form_processing",
        input_data={"device": form_data.get('device_name', 'N/A')},
        output_data={"fda_class": fda_class, "registry_ready": result.get('registry_submission_ready')},
        compliance_flags=compliance_flags
    )
    result['audit_id'] = audit['audit_id']
    result['timestamp'] = audit['timestamp']
    
    return result
