"""
Compliance guardrails for healthcare AI agents.
Enforces HIPAA, ICD-10, CPT, and payer-policy rules.
"""

HIPAA_PROHIBITED_FIELDS = [
    'ssn', 'social_security', 'full_name_with_dob',
    'account_number', 'certificate_number', 'vehicle_id',
    'device_serial', 'biometric', 'photo', 'ip_address'
]

VALID_ICD10_PREFIXES = [
    'A','B','C','D','E','F','G','H','I','J','K','L','M',
    'N','O','P','Q','R','S','T','U','V','W','X','Y','Z'
]

HIGH_RISK_CPT_CODES = {
    '99291': 'Critical care, first 30-74 minutes',
    '99292': 'Critical care, each additional 30 minutes',
    '33533': 'CABG using arterial graft, single',
    '27447': 'Total knee arthroplasty',
    '27130': 'Total hip arthroplasty',
    '22612': 'Lumbar arthrodesis posterior',
}

PRIOR_AUTH_REQUIRED_CPT = [
    '27447', '27130', '33533', '22612', '70553', '74178',
    '93306', '43239', '64483', '62323'
]

def check_icd10_format(code: str) -> dict:
    code = code.strip().upper()
    valid = (
        len(code) >= 3 and
        code[0] in VALID_ICD10_PREFIXES and
        code[1:3].isdigit()
    )
    return {
        "code": code,
        "valid_format": valid,
        "message": "Valid ICD-10 format" if valid else f"Invalid ICD-10 format: {code}"
    }

def check_cpt_format(code: str) -> dict:
    code = code.strip()
    valid = len(code) == 5 and code.isdigit()
    is_high_risk = code in HIGH_RISK_CPT_CODES
    requires_prior_auth = code in PRIOR_AUTH_REQUIRED_CPT
    return {
        "code": code,
        "valid_format": valid,
        "is_high_risk": is_high_risk,
        "requires_prior_auth": requires_prior_auth,
        "description": HIGH_RISK_CPT_CODES.get(code, "Standard procedure"),
        "message": "High-risk procedure - requires additional review" if is_high_risk else "Standard CPT code"
    }

def hipaa_phi_check(data: dict) -> dict:
    flags = []
    for key in data:
        for prohibited in HIPAA_PROHIBITED_FIELDS:
            if prohibited in key.lower():
                flags.append(f"Potential PHI field detected: {key}")
    return {
        "compliant": len(flags) == 0,
        "flags": flags,
        "recommendation": "Remove or de-identify PHI fields before processing" if flags else "No PHI violations detected"
    }

def medical_necessity_check(diagnosis_codes: list, procedure_codes: list) -> dict:
    """Basic medical necessity validation between diagnoses and procedures."""
    flags = []
    
    # Orthopedic procedures need musculoskeletal diagnoses
    ortho_cpt = {'27447', '27130', '22612'}
    ortho_icd_prefixes = ['M', 'S', 'T']
    
    has_ortho_proc = any(c in ortho_cpt for c in procedure_codes)
    has_ortho_diag = any(c[0] in ortho_icd_prefixes for c in diagnosis_codes if c)
    
    if has_ortho_proc and not has_ortho_diag:
        flags.append("Orthopedic procedure without supporting musculoskeletal diagnosis")
    
    # Cardiac procedures need cardiac diagnoses
    cardiac_cpt = {'33533'}
    cardiac_icd_prefixes = ['I']
    
    has_cardiac_proc = any(c in cardiac_cpt for c in procedure_codes)
    has_cardiac_diag = any(c[0] in cardiac_icd_prefixes for c in diagnosis_codes if c)
    
    if has_cardiac_proc and not has_cardiac_diag:
        flags.append("Cardiac procedure without supporting cardiac diagnosis")
    
    return {
        "medical_necessity_supported": len(flags) == 0,
        "flags": flags,
        "recommendation": "; ".join(flags) if flags else "Medical necessity criteria met"
    }

def validate_claim_amount(amount: float, cpt_code: str) -> dict:
    """Flag unusually high or low claim amounts."""
    # Simplified benchmark ranges (in USD)
    benchmarks = {
        '27447': (15000, 50000),
        '27130': (15000, 45000),
        '33533': (40000, 120000),
        '99213': (80, 300),
        '99214': (120, 400),
        '99215': (200, 600),
    }
    
    if cpt_code in benchmarks:
        low, high = benchmarks[cpt_code]
        if amount < low:
            return {"flag": "UNDER_BILLED", "message": f"Amount ${amount} is below expected range ${low}-${high}"}
        elif amount > high:
            return {"flag": "OVER_BILLED", "message": f"Amount ${amount} exceeds expected range ${low}-${high}"}
    
    return {"flag": "NORMAL", "message": "Amount within acceptable range"}
