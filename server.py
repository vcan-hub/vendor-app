"""
Vendor Registration Server
- Form submits to Google Apps Script → saved to your Google Sheet + Drive
- Dashboard reads live from your Google Sheet
"""

try:
    from flask import Flask, request, jsonify, send_file, redirect, abort
    from flask_cors import CORS
except ImportError:
    print("\n❌  Run this first:\n    pip install flask flask-cors requests\n")
    exit(1)

import os, base64, requests

# ════════════════════════════════════════════
#  SETTINGS
# ════════════════════════════════════════════
DASHBOARD_PASSWORD = "admin123"         # ← change this!
APPS_SCRIPT_URL    = "https://script.google.com/macros/s/AKfycbyoYXkkk5dEqyGPkGpwF6PIeCu2xv1eun3h8mIvxwr1EgNgoKG_q-t2r98_POMzA7E/exec"  # ← paste your Apps Script URL here
PORT = 5000
# ════════════════════════════════════════════

app  = Flask(__name__)
CORS(app)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
FORM_FILE = os.path.join(BASE_DIR, "form.html")

ALLOWED_EXT = {"pdf", "jpg", "jpeg", "png"}

def file_to_base64(file_obj):
    if not file_obj or not file_obj.filename:
        return None
    ext = file_obj.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return None
    data = base64.b64encode(file_obj.read()).decode("utf-8")
    return {"data": data, "mimeType": file_obj.content_type, "ext": ext}

# ── Serve form ──
@app.route("/")
def home():
    return send_file(FORM_FILE)

# ── Receive form submission ──
@app.route("/submit", methods=["POST"])
def submit():
    f = request.form
    payload = {
        "name": f.get("name",""), "address": f.get("address",""),
        "city": f.get("city",""), "pincode": f.get("pincode",""),
        "state": f.get("state",""), "country": f.get("country",""),
        "phone1": f.get("phone1",""), "phone2": f.get("phone2",""),
        "contactPerson": f.get("contactPerson",""), "designation": f.get("designation",""),
        "mobile": f.get("mobile",""), "email": f.get("email",""),
        "website": f.get("website",""), "msmeNo": f.get("msmeNo",""),
        "enterprisedCategory": f.get("enterprisedCategory",""),
        "tanNo": f.get("tanNo",""), "companyType": f.get("companyType",""),
        "panNo": f.get("panNo",""), "gstNo": f.get("gstNo",""),
        "billingName": f.get("billingName",""), "billingAddress": f.get("billingAddress",""),
        "billingCity": f.get("billingCity",""), "billingPincode": f.get("billingPincode",""),
        "billingState": f.get("billingState",""),
        "shippingName": f.get("shippingName",""), "shippingAddress": f.get("shippingAddress",""),
        "shippingCity": f.get("shippingCity",""), "shippingPincode": f.get("shippingPincode",""),
        "shippingState": f.get("shippingState",""),
        "bankName": f.get("bankName",""), "accountNo": f.get("accountNo",""),
        "ifsc": f.get("ifsc",""), "branch": f.get("branch",""),
        "accountType": f.get("accountType",""),
        "place": f.get("place",""), "date": f.get("date",""),
        "authorisedName": f.get("authorisedName",""),
        "docs": {
            "pan":    file_to_base64(request.files.get("doc_pan")),
            "gst":    file_to_base64(request.files.get("doc_gst")),
            "incorp": file_to_base64(request.files.get("doc_incorp")),
            "msme":   file_to_base64(request.files.get("doc_msme")),
            "cheque": file_to_base64(request.files.get("doc_cheque")),
        }
    }
    try:
        resp   = requests.post(APPS_SCRIPT_URL, json=payload, timeout=30)
        result = resp.json()
        if result.get("success"):
            return jsonify({"success": True, "id": result.get("row")})
        return jsonify({"success": False, "error": result.get("error","Unknown error")}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Proxy: fetch vendors from Apps Script for dashboard ──
@app.route("/api/vendors")
def api_vendors():
    if request.args.get("pwd") != DASHBOARD_PASSWORD:
        abort(403)
    try:
        resp = requests.get(APPS_SCRIPT_URL, params={"action": "getVendors"}, timeout=15)
        return jsonify(resp.json().get("vendors", []))
    except Exception as e:
        return jsonify([])

# ── Proxy: update vendor status ──
@app.route("/api/vendor/status", methods=["POST"])
def update_status():
    if request.args.get("pwd") != DASHBOARD_PASSWORD:
        abort(403)
    data = request.json
    try:
        requests.get(APPS_SCRIPT_URL, params={
            "action": "updateStatus",
            "row": data.get("row"),
            "status": data.get("status")
        }, timeout=10)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Dashboard ──
@app.route("/dashboard")
def dashboard():
    pwd = request.args.get("pwd", "")
    if pwd != DASHBOARD_PASSWORD:
        return """<!DOCTYPE html><html><head><title>Login</title>
        <style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;
        height:100vh;margin:0;background:#f7f8fc}
        .box{background:#fff;padding:40px;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,.1);text-align:center}
        h2{color:#1e3a5f;margin-bottom:20px}
        input{padding:10px 16px;border:1.5px solid #e2e8f0;border-radius:8px;font-size:1rem;width:240px}
        button{margin-top:16px;padding:10px 32px;background:#2563eb;color:#fff;border:none;
        border-radius:8px;font-size:1rem;cursor:pointer;width:100%}
        button:hover{background:#1d4ed8}</style></head>
        <body><div class="box"><h2>🔐 Dashboard Login</h2>
        <form method="get"><input name="pwd" type="password" placeholder="Enter password" autofocus>
        <button>Login</button></form></div></body></html>"""
    return DASHBOARD_HTML.replace("__PWD__", pwd)

# ─────────────────────────────────────────────
# Dashboard HTML
# ─────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vendor Dashboard</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'DM Sans',sans-serif;background:#f7f8fc;color:#1a1f2e}
.topbar{background:#1e3a5f;padding:18px 32px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.topbar h1{font-family:'DM Serif Display',serif;color:#fff;font-size:1.35rem}
.topbar small{color:#93c5fd;font-size:.8rem;display:block;margin-top:3px}
.tbr{display:flex;gap:10px;align-items:center}
.rbtn{padding:8px 18px;background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.3);border-radius:8px;font-size:.82rem;cursor:pointer;font-family:inherit}
.rbtn:hover{background:rgba(255,255,255,.25)}
.stats{display:flex;gap:16px;padding:24px 32px 0;flex-wrap:wrap}
.sc{background:#fff;border-radius:12px;padding:20px 28px;flex:1;min-width:130px;box-shadow:0 2px 12px rgba(0,0,0,.06);transition:transform .15s}
.sc:hover{transform:translateY(-2px)}
.sc .n{font-size:2rem;font-weight:700;color:#2563eb}
.sc .l{font-size:.75rem;color:#4a5568;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-top:2px}
.fb{display:flex;gap:12px;padding:20px 32px;flex-wrap:wrap;align-items:center}
.fb input,.fb select{padding:9px 14px;border:1.5px solid #e2e8f0;border-radius:8px;font-size:.88rem;outline:none;background:#fff;font-family:inherit}
.fb input{width:260px}.fb input:focus{border-color:#2563eb}
.tw{padding:0 32px 40px;overflow-x:auto}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.06)}
thead tr{background:#1e3a5f}
th{color:#fff;padding:13px 16px;font-size:.75rem;font-weight:600;letter-spacing:.8px;text-transform:uppercase;text-align:left;white-space:nowrap}
tbody tr{border-bottom:1px solid #e2e8f0;cursor:pointer;transition:background .15s}
tbody tr:hover{background:#eff6ff}tbody tr:last-child{border-bottom:none}
td{padding:12px 16px;font-size:.87rem;white-space:nowrap;max-width:200px;overflow:hidden;text-overflow:ellipsis}
.badge{padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:600;white-space:nowrap}
.bp{background:#fef3c7;color:#92400e}.ba{background:#d1fae5;color:#065f46}
.br{background:#fee2e2;color:#991b1b}.bu{background:#e0e7ff;color:#3730a3}
.loading{text-align:center;padding:60px;color:#aaa}
.spinner-big{width:40px;height:40px;border:3px solid #e2e8f0;border-top-color:#2563eb;border-radius:50%;animation:spin .7s linear infinite;margin:0 auto 16px}
@keyframes spin{to{transform:rotate(360deg)}}
.ov{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;overflow-y:auto;padding:32px 16px}
.ov.open{display:block}
.modal{background:#fff;border-radius:16px;max-width:820px;margin:0 auto;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.25)}
.mh{background:#1e3a5f;padding:22px 28px;display:flex;justify-content:space-between;align-items:flex-start}
.mh h2{color:#fff;font-family:'DM Serif Display',serif;font-size:1.15rem}
.mh small{color:#93c5fd;font-size:.8rem;display:block;margin-top:4px}
.xbtn{background:none;border:none;color:#93c5fd;font-size:1.5rem;cursor:pointer;line-height:1}.xbtn:hover{color:#fff}
.mb{padding:28px}
.ms{margin-bottom:22px}
.ms h3{font-size:.72rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#1e3a5f;background:#eff6ff;padding:7px 12px;border-radius:6px;margin-bottom:14px}
.mg{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.mg3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
.mf label{font-size:.7rem;font-weight:600;color:#4a5568;text-transform:uppercase;letter-spacing:.5px}
.mf p{font-size:.9rem;color:#1a1f2e;margin-top:3px;word-break:break-word}
.mf p.e{color:#ccc;font-style:italic}
.dlinks{display:flex;flex-wrap:wrap;gap:10px}
.dl{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:#eff6ff;color:#2563eb;border-radius:8px;font-size:.82rem;font-weight:600;text-decoration:none;border:1px solid #bfdbfe;transition:background .15s}
.dl:hover{background:#dbeafe}
.dl.no{background:#f9fafb;color:#bbb;border-color:#e2e8f0;pointer-events:none}
.ssel{padding:9px 14px;border:1.5px solid #e2e8f0;border-radius:8px;font-size:.88rem;background:#fff;cursor:pointer;font-family:inherit}
.ssb{padding:9px 22px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:.88rem;font-weight:600;cursor:pointer;margin-left:8px;font-family:inherit}
.ssb:hover{background:#1d4ed8}.ssb.saved{background:#059669}
@media(max-width:640px){.mg,.mg3{grid-template-columns:1fr}.stats{flex-direction:column}.tw,.stats,.fb{padding-left:16px;padding-right:16px}.fb input{width:100%}}
</style></head><body>

<div class="topbar">
  <div><h1>📊 Vendor Dashboard</h1><small id="ref">Loading…</small></div>
  <div class="tbr">
    <button class="rbtn" onclick="load()">🔄 Refresh</button>
  </div>
</div>

<div class="stats">
  <div class="sc"><div class="n" id="sT">—</div><div class="l">Total</div></div>
  <div class="sc"><div class="n" id="sP" style="color:#d97706">—</div><div class="l">Pending</div></div>
  <div class="sc"><div class="n" id="sU" style="color:#4f46e5">—</div><div class="l">Under Review</div></div>
  <div class="sc"><div class="n" id="sA" style="color:#059669">—</div><div class="l">Approved</div></div>
  <div class="sc"><div class="n" id="sR" style="color:#dc2626">—</div><div class="l">Rejected</div></div>
</div>

<div class="fb">
  <input id="si" placeholder="🔍  Search company, email, city, GST…" oninput="render()">
  <select id="sf" onchange="render()">
    <option value="">All Statuses</option>
    <option>Pending</option><option>Under Review</option>
    <option>Approved</option><option>Rejected</option>
  </select>
</div>

<div class="tw">
  <table>
    <thead><tr>
      <th>#</th><th>Submitted</th><th>Company</th><th>Contact</th>
      <th>Mobile</th><th>Email</th><th>City / State</th><th>GST No.</th>
      <th>Docs</th><th>Status</th>
    </tr></thead>
    <tbody id="tb">
      <tr><td colspan="10" class="loading">
        <div class="spinner-big"></div>Loading vendors…
      </td></tr>
    </tbody>
  </table>
</div>

<!-- Detail Modal -->
<div class="ov" id="ov" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <div class="mh">
      <div><h2 id="mt">Vendor Details</h2><small id="ms2"></small></div>
      <button class="xbtn" onclick="closeModal()">✕</button>
    </div>
    <div class="mb" id="mb"></div>
  </div>
</div>

<script>
const PWD = '__PWD__';
let all = [];

const bc = s => s==='Approved'?'ba':s==='Rejected'?'br':s==='Under Review'?'bu':'bp';
const fv = v => (v !== null && v !== undefined && String(v).trim()) ? String(v) : null;
const fd = v => fv(v) || '<span class="e">—</span>';
const fld = (l,v) => `<div class="mf"><label>${l}</label><p>${fd(v)}</p></div>`;
const dl = (l,u) => u ? `<a class="dl" href="${u}" target="_blank">📄 ${l}</a>`
                       : `<span class="dl no">— ${l}</span>`;
const docCount = v => [v['PAN Doc'],v['GST Doc'],v['Incorp Doc'],v['UDYAM Doc'],v['Cheque Doc']].filter(Boolean).length;

async function load() {
  document.getElementById('ref').textContent = 'Refreshing…';
  try {
    const r = await fetch('/api/vendors?pwd=' + PWD);
    all = await r.json();
    document.getElementById('ref').textContent = 'Last refreshed: ' + new Date().toLocaleTimeString('en-IN');
    updateStats();
    render();
  } catch(e) {
    document.getElementById('ref').textContent = 'Failed to load — check connection';
  }
}

function updateStats() {
  document.getElementById('sT').textContent = all.length;
  document.getElementById('sP').textContent = all.filter(v=>v['Status']==='Pending').length;
  document.getElementById('sU').textContent = all.filter(v=>v['Status']==='Under Review').length;
  document.getElementById('sA').textContent = all.filter(v=>v['Status']==='Approved').length;
  document.getElementById('sR').textContent = all.filter(v=>v['Status']==='Rejected').length;
}

function render() {
  const q  = document.getElementById('si').value.toLowerCase();
  const sf = document.getElementById('sf').value;
  const rows = all.filter(v => {
    const m = !q || [v['Company Name'],v['Email'],v['City'],v['Contact Person'],v['Mobile'],v['GST No.']].join(' ').toLowerCase().includes(q);
    return m && (!sf || v['Status'] === sf);
  });
  const tb = document.getElementById('tb');
  if (!rows.length) {
    tb.innerHTML = '<tr><td colspan="10" class="loading">No vendors found.</td></tr>';
    return;
  }
  tb.innerHTML = rows.map((v,i) => `
    <tr onclick="openModal(${v['_row']})">
      <td style="color:#aaa;font-size:.8rem">#${v['Row']||i+1}</td>
      <td style="color:#aaa;font-size:.8rem">${fv(v['Submitted At'])||'—'}</td>
      <td style="font-weight:600">${fv(v['Company Name'])||'—'}</td>
      <td>${fv(v['Contact Person'])||'—'}</td>
      <td>${fv(v['Mobile'])||'—'}</td>
      <td style="color:#2563eb">${fv(v['Email'])||'—'}</td>
      <td>${[fv(v['City']),fv(v['State'])].filter(Boolean).join(', ')||'—'}</td>
      <td style="font-family:monospace;font-size:.8rem">${fv(v['GST No.'])||'—'}</td>
      <td style="font-size:.82rem;color:#4a5568">${docCount(v)}/5 docs</td>
      <td><span class="badge ${bc(v['Status'])}">${v['Status']||'Pending'}</span></td>
    </tr>`).join('');
}

function openModal(row) {
  const v = all.find(x => x['_row'] === row);
  if (!v) return;
  document.getElementById('mt').textContent  = v['Company Name'] || 'Vendor Details';
  document.getElementById('ms2').textContent = `Submitted: ${v['Submitted At']||'—'} · Row #${v['Row']||row}`;
  document.getElementById('mb').innerHTML = `
    <div class="ms"><h3>Status</h3>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <select class="ssel" id="ss">${['Pending','Under Review','Approved','Rejected'].map(s=>`<option${s===v['Status']?' selected':''}>${s}</option>`).join('')}</select>
        <button class="ssb" id="ssb" onclick="saveStatus(${row})">Save Status</button>
      </div>
    </div>
    <div class="ms"><h3>Documents (in your Google Drive)</h3>
      <div class="dlinks">
        ${dl('PAN Card',        v['PAN Doc'])}
        ${dl('GST Certificate', v['GST Doc'])}
        ${dl('Incorp. Cert.',   v['Incorp Doc'])}
        ${dl('UDYAM Cert.',     v['UDYAM Doc'])}
        ${dl('Cancelled Cheque',v['Cheque Doc'])}
      </div>
    </div>
    <div class="ms"><h3>General Details</h3>
      <div class="mg">${fld('Company Name',v['Company Name'])}${fld('Company Type',v['Company Type'])}</div>
      <div style="margin-top:12px">${fld('Address',v['Address'])}</div>
      <div class="mg3" style="margin-top:12px">${fld('City',v['City'])}${fld('Pincode',v['Pincode'])}${fld('State',v['State'])}</div>
      <div class="mg3" style="margin-top:12px">${fld('Country',v['Country'])}${fld('Phone 1',v['Phone 1'])}${fld('Phone 2',v['Phone 2'])}</div>
      <div class="mg3" style="margin-top:12px">${fld('Contact Person',v['Contact Person'])}${fld('Designation',v['Designation'])}${fld('Mobile',v['Mobile'])}</div>
      <div class="mg3" style="margin-top:12px">${fld('Email',v['Email'])}${fld('Website',v['Website'])}${fld('MSME No.',v['MSME No.'])}</div>
      <div class="mg" style="margin-top:12px">${fld('Enterprise Category',v['Enterprise Category'])}${fld('TAN No.',v['TAN No.'])}</div>
    </div>
    <div class="ms"><h3>Tax Details</h3>
      <div class="mg">${fld('PAN No.',v['PAN No.'])}${fld('GST No.',v['GST No.'])}</div>
    </div>
    <div class="ms"><h3>Bank Details</h3>
      <div class="mg3">${fld('Bank Name',v['Bank Name'])}${fld('Account No.',v['Account No.'])}${fld('IFSC',v['IFSC'])}</div>
      <div class="mg" style="margin-top:12px">${fld('Branch',v['Branch'])}${fld('Account Type',v['Account Type'])}</div>
    </div>
    <div class="ms"><h3>Billing Address</h3>
      <div class="mg">${fld('Name',v['Billing Name'])}${fld('Address',v['Billing Address'])}${fld('City',v['Billing City'])}${fld('Pincode',v['Billing Pincode'])}</div>
    </div>
    <div class="ms"><h3>Shipping Address</h3>
      <div class="mg">${fld('Name',v['Shipping Name'])}${fld('Address',v['Shipping Address'])}${fld('City',v['Shipping City'])}${fld('Pincode',v['Shipping Pincode'])}</div>
    </div>
    <div class="ms"><h3>Declaration</h3>
      <div class="mg3">${fld('Place',v['Place'])}${fld('Date',v['Date'])}${fld('Authorised Signatory',v['Authorised Signatory'])}</div>
    </div>`;
  document.getElementById('ov').classList.add('open');
}

async function saveStatus(row) {
  const status = document.getElementById('ss').value;
  const btn    = document.getElementById('ssb');
  btn.textContent = 'Saving…'; btn.disabled = true;
  await fetch('/api/vendor/status?pwd=' + PWD, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ row, status })
  });
  const v = all.find(x => x['_row'] === row);
  if (v) v['Status'] = status;
  updateStats(); render();
  btn.textContent = '✓ Saved!'; btn.classList.add('saved');
  setTimeout(() => { btn.textContent = 'Save Status'; btn.classList.remove('saved'); btn.disabled = false; }, 2000);
}

function closeModal() { document.getElementById('ov').classList.remove('open'); }

load();
setInterval(load, 60000);
</script></body></html>"""

if __name__ == "__main__":
    print("\n" + "="*52)
    print("  ✅  Vendor Registration Server is running!")
    print("="*52)
    print(f"\n  📋  Form:       http://localhost:{PORT}/")
    print(f"  📊  Dashboard:  http://localhost:{PORT}/dashboard?pwd={DASHBOARD_PASSWORD}")
    print("\n  Press CTRL+C to stop\n")
    app.run(debug=False, host="0.0.0.0", port=PORT)
