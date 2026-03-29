from flask import Blueprint, request, jsonify
from agents.audit_agent import get_audit_logs, get_compliance_summary, generate_audit_report

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/logs', methods=['GET'])
def logs():
    limit = request.args.get('limit', 50, type=int)
    data = get_audit_logs(limit=limit)
    return jsonify({"logs": data, "count": len(data)})

@audit_bp.route('/summary', methods=['GET'])
def summary():
    return jsonify(get_compliance_summary())

@audit_bp.route('/report', methods=['POST'])
def report():
    data = request.get_json() or {}
    result = generate_audit_report(data.get('audit_ids'))
    return jsonify(result)
