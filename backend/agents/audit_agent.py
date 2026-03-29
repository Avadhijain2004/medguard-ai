"""
Audit Trail & Compliance Reporting Agent
Generates auditable reports of all agent decisions.
"""
import json
import os
from datetime import datetime
from utils.bedrock_client import invoke_claude

AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'audit_log.jsonl')

def get_audit_logs(limit: int = 50) -> list:
    logs = []
    if not os.path.exists(AUDIT_LOG_PATH):
        return logs
    with open(AUDIT_LOG_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return logs[-limit:]

def get_compliance_summary() -> dict:
    logs = get_audit_logs(limit=1000)
    
    total = len(logs)
    by_agent = {}
    total_flags = 0
    
    for log in logs:
        agent = log.get('agent', 'Unknown')
        by_agent[agent] = by_agent.get(agent, 0) + 1
        total_flags += len(log.get('compliance_flags', []))
    
    return {
        "total_transactions": total,
        "by_agent": by_agent,
        "total_compliance_flags": total_flags,
        "flag_rate": round(total_flags / max(total, 1), 2),
        "generated_at": datetime.utcnow().isoformat()
    }

def generate_audit_report(audit_ids: list = None) -> dict:
    logs = get_audit_logs()
    
    if audit_ids:
        logs = [l for l in logs if l.get('audit_id') in audit_ids]
    
    SYSTEM_PROMPT = """You are a Healthcare Compliance Audit Analyst. Generate a concise compliance report from audit log data.
    
OUTPUT FORMAT: Respond ONLY with valid JSON:
{
  "report_summary": "...",
  "high_priority_findings": ["..."],
  "compliance_rate": 0.0,
  "recommendations": ["..."],
  "regulatory_references": ["..."]
}"""
    
    user_message = f"""Generate a compliance audit report from these agent decision logs:

AUDIT LOGS:
{json.dumps(logs[-20:], indent=2)}

Identify patterns, flag high-risk findings, and provide recommendations."""
    
    try:
        raw_response = invoke_claude(SYSTEM_PROMPT, user_message, max_tokens=2048)
        raw_response = raw_response.strip()
        if raw_response.startswith("```"):
            raw_response = raw_response.split("```")[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]
        report = json.loads(raw_response)
    except Exception:
        report = {"report_summary": "Report generation failed", "high_priority_findings": [], "compliance_rate": 0}
    
    report['audit_logs'] = logs
    report['summary_stats'] = get_compliance_summary()
    report['generated_at'] = datetime.utcnow().isoformat()
    
    return report
