const API_BASE = '/api';

async function apiPost(endpoint, data) {
  const res = await fetch(API_BASE + endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function apiGet(endpoint) {
  const res = await fetch(API_BASE + endpoint);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function showLoading(containerId, msg = 'Running AI agent...') {
  document.getElementById(containerId).innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>${msg}</p>
    </div>`;
}

function showError(containerId, msg) {
  document.getElementById(containerId).innerHTML = `
    <div class="flags-list">
      <div class="flag-item error"><div class="flag-dot"></div>${msg}</div>
    </div>`;
}

function escapeHtml(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function formatTimestamp(ts) {
  if (!ts) return '—';
  try { return new Date(ts).toLocaleString(); } catch { return ts; }
}

function decisionClass(decision) {
  if (!decision) return '';
  const d = decision.toUpperCase();
  if (d.includes('APPROV')) return 'approved';
  if (d.includes('DENY') || d.includes('DENIED')) return 'denied';
  if (d.includes('PEND') || d.includes('RETURN')) return 'pending';
  if (d.includes('ESCALATE') || d.includes('REVIEW')) return 'review';
  if (d.includes('PAY')) return 'approved';
  return 'pending';
}

function decisionIcon(cls) {
  const icons = {
    approved: `<svg viewBox="0 0 20 20" fill="none"><path d="M5 10l4 4 6-7" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    denied: `<svg viewBox="0 0 20 20" fill="none"><path d="M6 6l8 8M14 6l-8 8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>`,
    pending: `<svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M10 7v3l2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
    review: `<svg viewBox="0 0 20 20" fill="none"><path d="M10 6v4M10 14h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.5"/></svg>`
  };
  return icons[cls] || icons.pending;
}

function renderFlags(flags, container) {
  if (!flags || !flags.length) {
    container.innerHTML = `<div class="flags-list"><div class="flag-item success"><div class="flag-dot"></div>No compliance flags — all checks passed</div></div>`;
    return;
  }
  container.innerHTML = `<div class="flags-list">${flags.map(f => `
    <div class="flag-item warning"><div class="flag-dot"></div>${escapeHtml(f)}</div>
  `).join('')}</div>`;
}

function renderConfidence(score, container) {
  const pct = Math.round((score || 0) * 100);
  container.innerHTML = `
    <div class="confidence-bar-wrap">
      <div class="confidence-label"><span>AI Confidence</span><span>${pct}%</span></div>
      <div class="confidence-bar"><div class="confidence-fill" style="width:${pct}%"></div></div>
    </div>`;
}

function renderAuditInfo(result, container) {
  container.innerHTML = `
    <div class="kv-list">
      <div class="kv-row"><span class="kv-key">Audit ID</span><span class="kv-value">${escapeHtml(result.audit_id)}</span></div>
      <div class="kv-row"><span class="kv-key">Timestamp</span><span class="kv-value">${formatTimestamp(result.timestamp)}</span></div>
    </div>`;
}