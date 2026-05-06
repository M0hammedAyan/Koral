"""
Test email alert directly.
Run: python test_email.py
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load .env manually
env = {}
try:
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
except FileNotFoundError:
    print("ERROR: .env file not found")
    exit(1)

SMTP_USER  = env.get("SMTP_USER", "")
SMTP_PASS  = env.get("SMTP_PASS", "")
SMTP_HOST  = env.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(env.get("SMTP_PORT", "587"))
ALERT_EMAIL = env.get("ALERT_EMAIL", "")

print("=== KORAL Email Test ===")
print(f"SMTP_USER   : {SMTP_USER}")
print(f"SMTP_PASS   : {SMTP_PASS[:4]}...{SMTP_PASS[-2:]} ({len(SMTP_PASS)} chars)")
print(f"SMTP_HOST   : {SMTP_HOST}:{SMTP_PORT}")
print(f"ALERT_EMAIL : {ALERT_EMAIL}")
print()

if not SMTP_USER or not SMTP_PASS or not ALERT_EMAIL:
    print("ERROR: SMTP_USER, SMTP_PASS, or ALERT_EMAIL is missing in .env")
    exit(1)

if len(SMTP_PASS) < 8:
    print("ERROR: SMTP_PASS looks too short. Should be 16 chars from Gmail App Passwords.")
    exit(1)

print("Connecting to Gmail SMTP...")

try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[KORAL TEST] Email Alert Working"
    msg["From"]    = f"KORAL Alerts <{SMTP_USER}>"
    msg["To"]      = ALERT_EMAIL

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;
                background:#0a0a0a;color:#e0e0e0;border-radius:12px;overflow:hidden">
      <div style="background:#00d4ff;padding:20px 24px">
        <h1 style="margin:0;color:#000;font-size:18px">KORAL Email Alert Test</h1>
      </div>
      <div style="padding:24px">
        <p>This is a test email from KORAL AI Engine.</p>
        <p>If you received this, email alerts are working correctly.</p>
        <p>Future critical incidents will be sent to: <strong>{ALERT_EMAIL}</strong></p>
        <div style="background:#111;border-left:4px solid #00d4ff;padding:12px;
                    border-radius:0 6px 6px 0;margin-top:16px;font-size:13px;color:#aaa">
          Sent by KORAL AI Engine using GPT-4o
        </div>
      </div>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        print("Logging in...")
        server.login(SMTP_USER, SMTP_PASS)
        print("Sending email...")
        server.sendmail(SMTP_USER, ALERT_EMAIL, msg.as_string())

    print()
    print("[OK] Email sent successfully!")
    print(f"     Check inbox: {ALERT_EMAIL}")
    print("     Also check Spam folder if not in inbox.")

except smtplib.SMTPAuthenticationError:
    print()
    print("[FAIL] Authentication failed.")
    print("  The app password is wrong or Gmail blocked it.")
    print("  Steps to fix:")
    print("  1. Go to https://myaccount.google.com/apppasswords")
    print("  2. Delete the old KORAL app password")
    print("  3. Create a new one")
    print("  4. Copy it WITHOUT spaces into .env as SMTP_PASS=xxxxxxxxxxxx")

except smtplib.SMTPException as e:
    print(f"[FAIL] SMTP error: {e}")

except Exception as e:
    print(f"[FAIL] {e}")
