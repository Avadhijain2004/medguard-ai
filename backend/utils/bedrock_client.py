import boto3
import json
import os
from datetime import datetime

def get_bedrock_client():
    return boto3.client(
        service_name='bedrock-runtime',
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN')
    )

MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"

def invoke_claude(system_prompt: str, user_message: str, max_tokens: int = 4096) -> dict:
    client = get_bedrock_client()
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}]
    }
    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body)
    )
    result = json.loads(response['body'].read())
    return result['content'][0]['text']

def log_audit_entry(agent_name: str, action: str, input_data: dict, output_data: dict, compliance_flags: list = None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent_name,
        "action": action,
        "input_summary": str(input_data)[:500],
        "output_summary": str(output_data)[:500],
        "compliance_flags": compliance_flags or [],
        "audit_id": f"AUD-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    }
    # In production, persist to DB. For demo, log to file.
    log_path = os.path.join(os.path.dirname(__file__), '..', 'audit_log.jsonl')
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    return entry
