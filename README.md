# MedGuard AI — Healthcare Compliance Platform

**5 Domain-Specialized AI Agents with Compliance Guardrails**

---

## Overview

MedGuard AI is a production-grade healthcare compliance platform powered by Claude (AWS Bedrock). It implements 5 specialized AI agents that handle critical healthcare workflows — medical coding, prior authorization, claims adjudication, medical device implant form processing, and compliance auditing — with full regulatory guardrails and auditable reasoning at every step.

---

## Agents

| # | Agent | Domain | Key Standards |
|---|-------|--------|---------------|
| 1 | Medical Coding Agent | ICD-10-CM, CPT assignment | UHDDS, AHIMA, AMA guidelines |
| 2 | Prior Authorization Agent | Auth evaluation | InterQual, MCG, LCD criteria |
| 3 | Claims Adjudication Agent | Claim processing | NCCI edits, RBRVS, DRG |
| 4 | Device Implant Form Agent | UDI/FDA compliance | FDA 21 CFR Part 830, UDI Rule |
| 5 | Audit Trail Agent | Compliance reporting | HIPAA audit requirements |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JS |
| Backend | Python Flask |
| AI Model | Claude (via AWS Bedrock) |
| Compliance | Custom guardrails engine |

---

## Project Structure

```
medguard/
├── frontend/
│   ├── index.html              # Dashboard
│   ├── css/style.css           # All styles
│   ├── js/api.js               # Frontend utilities
│   └── pages/
│       ├── medical-coding.html
│       ├── prior-auth.html
│       ├── claims.html
│       ├── device-form.html
│       └── audit.html
├── backend/
│   ├── app.py                  # Flask entrypoint
│   ├── requirements.txt
│   ├── agents/
│   │   ├── medical_coding_agent.py
│   │   ├── prior_auth_agent.py
│   │   ├── claims_adjudication_agent.py
│   │   ├── device_form_agent.py
│   │   └── audit_agent.py
│   ├── routes/
│   │   ├── medical_coding.py
│   │   ├── prior_auth.py
│   │   ├── claims.py
│   │   ├── device_form.py
│   │   └── audit.py
│   └── utils/
│       ├── bedrock_client.py   # AWS Bedrock client + audit logging
│       └── compliance.py       # Guardrails engine
└── docs/
    ├── architecture.md
    └── impact_model.md
```

---

## Setup Instructions

### Prerequisites
- Python 3.9+
- AWS credentials with Bedrock access (Claude Sonnet 4)
- A modern web browser

### 1. Clone & Configure

```bash
git clone https://github.com/Avadhijain2004/medguard-ai.git
cd medguard-ai
```

Create `backend/.env`:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_DEFAULT_REGION=us-east-1
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Start the Backend

```bash
cd backend
python app.py
```

The API will run on `http://localhost:5000`

### 4. Open the Frontend

Open `frontend/index.html` in your browser. No build step required.

For best results, serve via a simple HTTP server:
```bash
cd frontend
python -m http.server 8080
```
Then visit `http://localhost:8080`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/medical-coding/analyze` | Run medical coding agent |
| GET | `/api/medical-coding/sample` | Get sample clinical note |
| POST | `/api/prior-auth/evaluate` | Evaluate auth request |
| GET | `/api/prior-auth/sample` | Get sample auth request |
| POST | `/api/claims/adjudicate` | Adjudicate a claim |
| GET | `/api/claims/sample` | Get sample claim |
| POST | `/api/device-form/process` | Process implant form |
| GET | `/api/device-form/sample` | Get sample device form |
| GET | `/api/audit/logs` | Get audit log entries |
| GET | `/api/audit/summary` | Get compliance summary |
| POST | `/api/audit/report` | Generate AI audit report |
| GET | `/api/health` | Health check |

---

## Compliance Guardrails

Every agent enforces these guardrails **at the code level**, independent of AI output:

1. **ICD-10 Format Validation** — Regex + prefix checks before any code is accepted
2. **CPT High-Risk Flagging** — Hardcoded list of high-risk procedures requiring co-sign
3. **Prior Auth Requirements** — CPT codes requiring auth are always flagged
4. **Medical Necessity Cross-check** — Diagnosis/procedure alignment validation
5. **Amount Benchmarking** — Billed amounts checked against procedure benchmarks
6. **HIPAA PHI Detection** — Field name scanning for prohibited identifiers
7. **FDA Device Classification** — Class III devices trigger mandatory escalation
8. **Recall Flag Enforcement** — Recalled devices blocked immediately
9. **Full Audit Trail** — Every agent decision logged with timestamp and audit ID

---

## Running a Demo

1. Open Medical Coding → Click "Load Sample Note" → Click "Run Coding Agent"
2. Open Prior Authorization → Click "Load Sample Request" → Click "Evaluate Authorization"
3. Open Claims → Click "Load Sample Claim" → Click "Adjudicate Claim"
4. Open Device Implant Form → Click "Load Sample Form" → Click "Process Implant Form"
5. Open Audit Trail → View all logged decisions with compliance flags
