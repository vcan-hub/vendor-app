"""
Vendor Registration Server
- Receives form + file uploads
- Sends everything to Google Apps Script
- Google Apps Script saves to YOUR Google Sheet + Drive
- No credentials file needed!
"""

try:
    from flask import Flask, request, jsonify, send_file, abort
    from flask_cors import CORS
except ImportError:
    print("\n❌  Run this first:\n")
    print("    pip install flask flask-cors requests\n")
    exit(1)

import os, json, base64, requests
from datetime import datetime

# ════════════════════════════════════════════
#  SETTINGS — fill these in!
# ════════════════════════════════════════════
DASHBOARD_PASSWORD = "admin123"        # ← change this!
APPS_SCRIPT_URL    = "https://script.google.com/macros/s/AKfycbwj0WUX6ZYK3C1lzT3Gn2B3G8eJ9RbKuaHA7lJqhskkmmkyhxXp_fxQdRUa3rlKPoLu/exec" # ← paste your Apps Script URL here (Step 2 of setup)
PORT = 5000
# ════════════════════════════════════════════

app  = Flask(__name__)
CORS(app)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
FORM_FILE = os.path.join(BASE_DIR, "form.html")

ALLOWED_EXT = {"pdf", "jpg", "jpeg", "png"}

def file_to_base64(file_obj):
    """Convert uploaded file to base64 so we can send it as JSON."""
    if not file_obj or not file_obj.filename:
        return None
    ext = file_obj.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return None
    data = base64.b64encode(file_obj.read()).decode("utf-8")
    return {"data": data, "mimeType": file_obj.content_type, "ext": ext}

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def home():
    return send_file(FORM_FILE)

@app.route("/submit", methods=["POST"])
def submit():
    f = request.form

    # Build payload — all form fields + files as base64
    payload = {
        # General
        "name":                f.get("name", ""),
        "address":             f.get("address", ""),
        "city":                f.get("city", ""),
        "pincode":             f.get("pincode", ""),
        "state":               f.get("state", ""),
        "country":             f.get("country", ""),
        "phone1":              f.get("phone1", ""),
        "phone2":              f.get("phone2", ""),
        "contactPerson":       f.get("contactPerson", ""),
        "designation":         f.get("designation", ""),
        "mobile":              f.get("mobile", ""),
        "email":               f.get("email", ""),
        "website":             f.get("website", ""),
        "msmeNo":              f.get("msmeNo", ""),
        "enterprisedCategory": f.get("enterprisedCategory", ""),
        "tanNo":               f.get("tanNo", ""),
        "companyType":         f.get("companyType", ""),
        "panNo":               f.get("panNo", ""),
        "gstNo":               f.get("gstNo", ""),
        # Billing
        "billingName":         f.get("billingName", ""),
        "billingAddress":      f.get("billingAddress", ""),
        "billingCity":         f.get("billingCity", ""),
        "billingPincode":      f.get("billingPincode", ""),
        "billingState":        f.get("billingState", ""),
        # Shipping
        "shippingName":        f.get("shippingName", ""),
        "shippingAddress":     f.get("shippingAddress", ""),
        "shippingCity":        f.get("shippingCity", ""),
        "shippingPincode":     f.get("shippingPincode", ""),
        "shippingState":       f.get("shippingState", ""),
        # Bank
        "bankName":            f.get("bankName", ""),
        "accountNo":           f.get("accountNo", ""),
        "ifsc":                f.get("ifsc", ""),
        "branch":              f.get("branch", ""),
        "accountType":         f.get("accountType", ""),
        # Declaration
        "place":               f.get("place", ""),
        "date":                f.get("date", ""),
        "authorisedName":      f.get("authorisedName", ""),
        # Documents (base64 encoded)
        "docs": {
            "pan":    file_to_base64(request.files.get("doc_pan")),
            "gst":    file_to_base64(request.files.get("doc_gst")),
            "incorp": file_to_base64(request.files.get("doc_incorp")),
            "msme":   file_to_base64(request.files.get("doc_msme")),
            "cheque": file_to_base64(request.files.get("doc_cheque")),
        }
    }

    # Send to Google Apps Script
    try:
        resp = requests.post(
            APPS_SCRIPT_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        result = resp.json()
        if result.get("success"):
            return jsonify({"success": True, "id": result.get("id")})
        else:
            return jsonify({"success": False, "error": result.get("error", "Unknown error")}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/dashboard")
def dashboard():
    pwd = request.args.get("pwd", "")
    if pwd != DASHBOARD_PASSWORD:
        return """
        <html><head><title>Login</title>
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

    # Redirect to Google Sheet as the live dashboard
    sheet_url = "https://docs.google.com/spreadsheets"
    return f"""
    <html><head><title>Dashboard</title>
    <style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;
    height:100vh;margin:0;background:#f7f8fc;flex-direction:column;gap:20px}}
    .box{{background:#fff;padding:40px 50px;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,.1);text-align:center}}
    h2{{color:#1e3a5f;margin-bottom:8px}}p{{color:#4a5568;margin-bottom:24px;font-size:.9rem}}
    .btn{{display:inline-block;padding:12px 28px;background:#059669;color:#fff;border-radius:8px;
    text-decoration:none;font-weight:600;font-size:.95rem;margin:6px}}
    .btn:hover{{background:#047857}}
    .btn2{{background:#2563eb}}.btn2:hover{{background:#1d4ed8}}</style></head>
    <body><div class="box">
      <h2>📊 Vendor Dashboard</h2>
      <p>Your data is stored securely in your own Google account.</p>
      <a class="btn" href="https://docs.google.com/spreadsheets" target="_blank">
        📋 Open Google Sheets
      </a>
      <a class="btn btn2" href="https://drive.google.com/drive/folders" target="_blank">
        📁 Open Google Drive
      </a>
    </div></body></html>"""

# ─────────────────────────────────────────────
# Start
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*52)
    print("  ✅  Vendor Registration Server is running!")
    print("="*52)
    print(f"\n  📋  Form:       http://localhost:{PORT}/")
    print(f"  📊  Dashboard:  http://localhost:{PORT}/dashboard?pwd={DASHBOARD_PASSWORD}")
    print("\n  Press CTRL+C to stop\n")
    app.run(debug=False, host="0.0.0.0", port=PORT)
