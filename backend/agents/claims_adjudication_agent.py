"""
Claims Adjudication Agent
Processes and adjudicates medical claims with full compliance enforcement.
"""
import json
from utils.bedrock_client import invoke_claude, log_audit_entry
from utils.compliance import check_icd10_format, check_cpt_format, validate_claim_amount, hipaa_phi_check

SYSTEM_PROMPT = """You are a Claims Adjudication AI Agent for a healthcare payer.

Your responsibilities:
1. Validate claim completeness (all required fields present)
2. Verify member eligibility and benefits
3. Check coordination of benefits (COB)
4. Apply fee schedule and contractual adjustments
5. Identify billing errors, upcoding, unbundling
6. Apply correct payment methodology (DRG, APC, RBRVS)
7. Flag potential fraud, waste, and abuse indicators

ADJUDICATION RULES:
- Apply National Correct Coding Initiative (NCCI) edits
- Enforce timely filing limits (180 days for most payers)
- Apply global surgery periods
- Check for duplicate claims
- Validate place of service codes
- Verify rendering provider credentials

FRAUD INDICATORS TO FLAG:
- Billing for services not rendered
- Upcoding (billing higher complexity than documented)
- Unbundling (billing components separately when global code applies)
- Phantom billing
- Service date anomalies

OUTPUT FORMAT: Respond ONLY with valid JSON:
{
  "adjudication_decision": "PAY|PARTIAL_PAY|DENY|PEND|RETURN_TO_PROVIDER",
  "allowed_amount": 0.00,
  "patient_responsibility": 0.00,
  "plan_payment": 0.00,
  "denial_codes": [{"code": "...", "description": "..."}],
  "remark_codes": [{"code": "...", "description": "..."}],
  "ncci_edits_applied": ["..."],
  "fraud_indicators": ["..."],
  "billing_errors": ["..."],
  "adjustment_reasons": [{"code": "...", "amount": 0.00, "reason": "..."}],
  "payment_methodology": "...",
  "processing_notes": ["..."],
  "requires_clinical_review": false,
  "confidence_score": 0.0
}"""

def run_claims_adjudication_agent(claim_data: dict) -> dict:
    agent_name = "ClaimsAdjudicationAgent"
    
    # HIPAA check first
    phi_check = hipaa_phi_check(claim_data)
    
    # Validate codes
    cpt_code = claim_data.get('procedure_code', '')
    icd_code = claim_data.get('diagnosis_code', '')
    billed_amount = float(claim_data.get('billed_amount', 0))
    
    cpt_validation = check_cpt_format(cpt_code)
    icd_validation = check_icd10_format(icd_code)
    amount_check = validate_claim_amount(billed_amount, cpt_code)
    
    user_message = f"""Adjudicate this medical claim:

CLAIM DATA:
{json.dumps(claim_data, indent=2)}

PRE-VALIDATION RESULTS:
- CPT Validation: {json.dumps(cpt_validation)}
- ICD-10 Validation: {json.dumps(icd_validation)}
- Amount Check: {json.dumps(amount_check)}

Apply all NCCI edits, fee schedules, and fraud detection rules. Provide complete adjudication decision."""

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

    compliance_flags = []
    
    if not phi_check['compliant']:
        compliance_flags.extend(phi_check['flags'])
    
    if amount_check['flag'] == 'OVER_BILLED':
        compliance_flags.append(f"OVERBILLING_FLAG: {amount_check['message']}")
        result['fraud_indicators'] = result.get('fraud_indicators', []) + [amount_check['message']]
    
    if not icd_validation['valid_format']:
        compliance_flags.append(f"INVALID_ICD10: {icd_validation['message']}")
        result['adjudication_decision'] = 'RETURN_TO_PROVIDER'
    
    if not cpt_validation['valid_format']:
        compliance_flags.append(f"INVALID_CPT: {cpt_code}")
        result['adjudication_decision'] = 'RETURN_TO_PROVIDER'
    
    result['compliance_flags'] = compliance_flags
    result['phi_check'] = phi_check
    result['code_validations'] = {
        'cpt': cpt_validation,
        'icd10': icd_validation,
        'amount': amount_check
    }
    
    # Generate claim number
    import hashlib, time
    claim_hash = hashlib.md5(f"{cpt_code}{icd_code}{time.time()}".encode()).hexdigest()[:10].upper()
    result['claim_number'] = f"CLM-{claim_hash}"
    
    audit = log_audit_entry(
        agent_name=agent_name,
        action="claims_adjudication",
        input_data={"cpt": cpt_code, "icd": icd_code, "amount": billed_amount},
        output_data={"decision": result.get('adjudication_decision'), "plan_payment": result.get('plan_payment')},
        compliance_flags=compliance_flags
    )
    result['audit_id'] = audit['audit_id']
    result['timestamp'] = audit['timestamp']
    
    return result
