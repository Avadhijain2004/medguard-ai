# MedGuard AI — Architecture Document

## System Overview

MedGuard AI is a multi-agent healthcare compliance platform. Five specialized AI agents are orchestrated through a Flask API backend, each powered by Claude via AWS Bedrock. Every agent decision is validated through a compliance guardrails engine before results are returned, and every action is persisted to an immutable audit log.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Browser)                        │
│   HTML/CSS/JS — 5 Agent Pages + Dashboard + Audit Trail          │
└─────────────────────┬───────────────────────────────────────────┘
                      │ REST (JSON)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FLASK API BACKEND                            │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ /medical-│  │/prior-   │  │ /claims  │  │ /device-form  │  │
│  │  coding  │  │  auth    │  │          │  │               │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬────────┘  │
│       │              │              │                │            │
│       ▼              ▼              ▼                ▼            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              AGENT ORCHESTRATION LAYER                   │    │
│  │                                                          │    │
│  │  Agent 1        Agent 2        Agent 3        Agent 4   │    │
│  │  Medical        Prior          Claims         Device    │    │
│  │  Coding         Auth           Adjudication   Implant   │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │         COMPLIANCE GUARDRAILS ENGINE             │   │    │
│  │  │  ICD-10 Validation │ CPT Risk │ HIPAA PHI Check  │   │    │
│  │  │  Medical Necessity │ Auth Req │ FDA Class Rules   │   │    │
│  │  │  Amount Benchmarks │ NCCI Edit│ Recall Blocking  │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  Agent 5: Audit Trail (reads audit_log.jsonl)           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                      │
│                            ▼                                      │
│                   ┌────────────────┐                             │
│                   │  AUDIT LOGGER  │                             │
│                   │ audit_log.jsonl│                             │
│                   └────────────────┘                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS (Bedrock API)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS BEDROCK                                    │
│           Claude Sonnet 4 (claude-sonnet-4-5)                   │
│                                                                  │
│  System Prompt: Domain-specific persona + guardrail rules        │
│  User Message:  Structured clinical/claim data                   │
│  Response:      Structured JSON with rationale + citations       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Roles & Responsibilities

### Agent 1 — Medical Coding Agent
**Purpose:** Extract and assign ICD-10-CM diagnosis codes and CPT procedure codes from unstructured clinical documentation.

**Input:** Free-text clinical notes, operative reports, discharge summaries

**Processing:**
1. Claude analyzes note against UHDDS and AHIMA coding guidelines
2. Assigns principal + secondary ICD-10 codes with rationale
3. Assigns CPT codes with modifier recommendations
4. Guardrails validate code format, detect high-risk procedures, check medical necessity alignment

**Output:** Structured JSON with codes, rationale, compliance flags, audit ID

---

### Agent 2 — Prior Authorization Agent
**Purpose:** Evaluate prior authorization requests against payer-specific clinical criteria.

**Input:** Member demographics, procedure code, diagnosis codes, clinical justification

**Processing:**
1. Claude evaluates request against InterQual/MCG criteria
2. Checks LCD (Local Coverage Determination) requirements
3. Evaluates step therapy compliance
4. Guardrails enforce escalation for high-risk/experimental procedures

**Output:** Approve/Deny/Pend decision with criteria evaluation, authorization number if approved

---

### Agent 3 — Claims Adjudication Agent
**Purpose:** Process medical claims through complete adjudication workflow.

**Input:** Claim header (member, provider, dates), procedure/diagnosis codes, billed amount

**Processing:**
1. HIPAA PHI field scan (pre-validation)
2. Code format validation (pre-validation)
3. Amount benchmarking against fee schedule ranges
4. Claude applies NCCI edits, fraud detection, payment methodology
5. Returns payment decision with denial/remark codes

**Output:** PAY/DENY/PEND decision with allowed amount, patient responsibility, fraud flags

---

### Agent 4 — Device Implant Form Agent (Hackathon Focus)
**Purpose:** Intelligent processing of medical device implant documentation with FDA compliance validation.

**Input:** Device details (name, manufacturer, UDI, lot/serial numbers, implant metadata)

**Processing:**
1. Claude extracts and structures device information
2. Validates UDI Device Identifier (DI) format
3. Determines FDA class (I/II/III) and clearance type
4. Generates ICD-10-PCS codes for device-related procedures
5. Guardrails: Class III escalation, recall blocking, missing field detection

**Output:** Structured device record, compliance status, registry submission readiness, tracking ID

---

### Agent 5 — Audit Trail Agent
**Purpose:** Maintain immutable audit log and generate compliance reports.

**Processing:**
- Reads all entries from `audit_log.jsonl` (append-only)
- Calculates compliance statistics by agent
- Can invoke Claude to generate narrative compliance reports

**Output:** Transaction log, compliance summary, AI-generated audit report

---

## Communication & Data Flow

```
Request → Route Handler → Agent → [Claude API] → Guardrails → Audit Log → Response
```

1. **Frontend** sends JSON POST to Flask route
2. **Route Handler** validates required fields
3. **Agent** constructs structured prompt with domain-specific system prompt
4. **Claude** returns structured JSON reasoning
5. **Guardrails Engine** validates and enriches Claude's output (code-level checks, never bypassed)
6. **Audit Logger** appends immutable entry with timestamp, agent, action, flags
7. **Response** returned to frontend with full decision + audit ID

---

## Error Handling Strategy

| Error Type | Handling |
|-----------|----------|
| Claude API failure | 500 returned with error message; no partial data |
| Invalid JSON from Claude | Fallback with raw response + parse error flag |
| Invalid ICD-10 format | Decision overridden to RETURN_TO_PROVIDER |
| Invalid CPT format | Decision overridden to RETURN_TO_PROVIDER |
| Recall flag detected | Status set to HOLD; compliance flag raised |
| Class III device | Mandatory escalation flag; cannot be suppressed |
| Overbilling detected | Fraud indicator added; clinical review flagged |

---

## Security Considerations

- AWS credentials loaded from `.env` (never committed)
- No PHI stored beyond the append-only audit log
- HIPAA PHI field scanning on every claims submission
- CORS restricted to localhost in development
- All agent outputs include audit IDs for traceability
