"""
Medical Coding Agent
Assigns ICD-10 diagnosis codes and CPT procedure codes from clinical notes.
Enforces coding compliance at every step.
"""
import json
from utils.bedrock_client import invoke_claude, log_audit_entry
from utils.compliance import check_icd10_format, check_cpt_format, medical_necessity_check

SYSTEM_PROMPT = """You are a Certified Professional Coder (CPC) and medical coding AI agent with expertise in ICD-10-CM, ICD-10-PCS, and CPT coding systems.

Your responsibilities:
1. Extract diagnoses and procedures from clinical documentation
2. Assign accurate ICD-10 diagnosis codes (principal + secondary)
3. Assign accurate CPT procedure codes
4. Apply official coding guidelines (UHDDS, AHIMA, AMA)
5. Flag any coding compliance concerns
6. Provide rationale for every code assigned

GUARDRAILS YOU MUST ALWAYS FOLLOW:
- Never assign codes not supported by clinical documentation
- Always code to the highest level of specificity
- Flag unbundling violations (CPT codes that cannot be billed together)
- Apply correct modifier usage
- Note when documentation is insufficient for accurate coding
- Cite the specific guideline or policy supporting each code assignment

OUTPUT FORMAT: Respond ONLY with valid JSON matching this exact structure:
{
  "principal_diagnosis": {"code": "...", "description": "...", "rationale": "..."},
  "secondary_diagnoses": [{"code": "...", "description": "...", "rationale": "..."}],
  "procedure_codes": [{"code": "...", "description": "...", "modifier": "...", "rationale": "..."}],
  "documentation_gaps": ["..."],
  "compliance_notes": ["..."],
  "confidence_score": 0.0,
  "coding_guidelines_applied": ["..."]
}"""

def run_medical_coding_agent(clinical_note: str, patient_context: dict = None) -> dict:
    agent_name = "MedicalCodingAgent"
    
    user_message = f"""Analyze the following clinical documentation and assign appropriate ICD-10 and CPT codes.

CLINICAL DOCUMENTATION:
{clinical_note}

PATIENT CONTEXT:
{json.dumps(patient_context or {}, indent=2)}

Apply all official coding guidelines. Flag any compliance concerns. Provide complete rationale."""

    raw_response = invoke_claude(SYSTEM_PROMPT, user_message)
    
    try:
        # Clean JSON response
        raw_response = raw_response.strip()
        if raw_response.startswith("```"):
            raw_response = raw_response.split("```")[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]
        coding_result = json.loads(raw_response)
    except json.JSONDecodeError:
        coding_result = {"error": "Failed to parse AI response", "raw": raw_response}
        return coding_result

    # Validate ICD-10 codes
    icd_validations = []
    all_icd_codes = []
    
    if coding_result.get('principal_diagnosis'):
        code = coding_result['principal_diagnosis'].get('code', '')
        validation = check_icd10_format(code)
        icd_validations.append(validation)
        all_icd_codes.append(code)
    
    for dx in coding_result.get('secondary_diagnoses', []):
        code = dx.get('code', '')
        validation = check_icd10_format(code)
        icd_validations.append(validation)
        all_icd_codes.append(code)

    # Validate CPT codes
    cpt_validations = []
    all_cpt_codes = []
    
    for proc in coding_result.get('procedure_codes', []):
        code = proc.get('code', '')
        validation = check_cpt_format(code)
        cpt_validations.append(validation)
        all_cpt_codes.append(code)
        
        # Add prior auth flag to procedure
        if validation.get('requires_prior_auth'):
            proc['prior_auth_required'] = True
            proc['compliance_flag'] = "PRIOR_AUTH_REQUIRED"

    # Medical necessity check
    necessity_result = medical_necessity_check(all_icd_codes, all_cpt_codes)
    
    # Compile compliance summary
    compliance_flags = []
    for v in icd_validations:
        if not v.get('valid_format'):
            compliance_flags.append(f"ICD-10 Format Error: {v['message']}")
    for v in cpt_validations:
        if v.get('is_high_risk'):
            compliance_flags.append(f"High-Risk CPT: {v['code']} - {v['description']}")
        if v.get('requires_prior_auth'):
            compliance_flags.append(f"Prior Auth Required: CPT {v['code']}")
    if not necessity_result['medical_necessity_supported']:
        compliance_flags.extend(necessity_result['flags'])

    coding_result['icd_validations'] = icd_validations
    coding_result['cpt_validations'] = cpt_validations
    coding_result['medical_necessity'] = necessity_result
    coding_result['compliance_flags'] = compliance_flags
    coding_result['requires_human_review'] = len(compliance_flags) > 0

    audit = log_audit_entry(
        agent_name=agent_name,
        action="medical_coding",
        input_data={"note_length": len(clinical_note)},
        output_data={"codes_assigned": len(all_icd_codes) + len(all_cpt_codes)},
        compliance_flags=compliance_flags
    )
    coding_result['audit_id'] = audit['audit_id']
    coding_result['timestamp'] = audit['timestamp']
    
    return coding_result
