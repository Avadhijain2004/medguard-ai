"""
Prior Authorization Agent
Evaluates prior auth requests against payer policies and clinical criteria.
"""
import json
from utils.bedrock_client import invoke_claude, log_audit_entry
from utils.compliance import check_cpt_format, PRIOR_AUTH_REQUIRED_CPT

SYSTEM_PROMPT = """You are a Prior Authorization Clinical Review Agent for a healthcare payer organization.

Your role is to evaluate prior authorization requests against:
1. Medicare/Medicaid Local Coverage Determinations (LCDs)
2. Commercial payer clinical criteria (InterQual, MCG guidelines)
3. FDA-approved indications for devices and medications
4. Medical necessity criteria
5. Step therapy requirements

DECISION FRAMEWORK:
- APPROVED: All criteria met, documentation sufficient
- APPROVED_WITH_CONDITIONS: Criteria met with specific requirements (e.g., follow-up)
- PEND_FOR_INFORMATION: Missing critical clinical documentation
- DENIED_NOT_MEDICALLY_NECESSARY: Clinical criteria not met
- DENIED_EXPERIMENTAL: Procedure/device not covered
- ESCALATE_TO_PHYSICIAN: Complex case requiring physician reviewer

GUARDRAILS:
- Never approve without documented diagnosis supporting medical necessity
- Always cite specific clinical criteria or policy referenced
- Flag cases involving experimental/investigational procedures
- Require step therapy documentation for applicable procedures
- Document every decision point with specific reasoning
- Identify appeal rights when denying

OUTPUT FORMAT: Respond ONLY with valid JSON:
{
  "decision": "APPROVED|APPROVED_WITH_CONDITIONS|PEND_FOR_INFORMATION|DENIED_NOT_MEDICALLY_NECESSARY|DENIED_EXPERIMENTAL|ESCALATE_TO_PHYSICIAN",
  "decision_rationale": "...",
  "criteria_evaluated": [{"criterion": "...", "met": true/false, "evidence": "..."}],
  "missing_documentation": ["..."],
  "conditions_if_approved": ["..."],
  "denial_reason_code": "...",
  "appeal_rights": "...",
  "clinical_guidelines_cited": ["..."],
  "estimated_review_time_days": 0,
  "confidence_score": 0.0,
  "flags": ["..."]
}"""

def run_prior_auth_agent(request_data: dict) -> dict:
    agent_name = "PriorAuthAgent"

    user_message = f"""Evaluate this prior authorization request:

REQUEST DETAILS:
{json.dumps(request_data, indent=2)}

Apply all relevant clinical criteria. Cite specific guidelines. Make a clear decision with full rationale."""

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

    # Apply guardrails
    cpt_code = request_data.get('procedure_code', '')
    cpt_check = check_cpt_format(cpt_code)
    
    compliance_flags = result.get('flags', [])
    
    if cpt_check.get('is_high_risk'):
        compliance_flags.append(f"HIGH_RISK_PROCEDURE: Requires attending physician co-signature")
        result['requires_physician_cosign'] = True
    
    # Auto-escalate experimental procedures
    if 'EXPERIMENTAL' in result.get('decision', ''):
        compliance_flags.append("EXPERIMENTAL_PROCEDURE: Mandatory medical director review")
        result['decision'] = 'ESCALATE_TO_PHYSICIAN'
    
    result['compliance_flags'] = compliance_flags
    result['procedure_risk_level'] = 'HIGH' if cpt_check.get('is_high_risk') else 'STANDARD'
    
    # Generate auth number if approved
    if result.get('decision', '').startswith('APPROVED'):
        import hashlib, time
        auth_hash = hashlib.md5(f"{cpt_code}{time.time()}".encode()).hexdigest()[:8].upper()
        result['authorization_number'] = f"AUTH-{auth_hash}"
        result['valid_days'] = 90
    
    audit = log_audit_entry(
        agent_name=agent_name,
        action="prior_auth_review",
        input_data={"cpt": cpt_code, "member_id": request_data.get('member_id', 'N/A')},
        output_data={"decision": result.get('decision')},
        compliance_flags=compliance_flags
    )
    result['audit_id'] = audit['audit_id']
    result['timestamp'] = audit['timestamp']
    
    return result
