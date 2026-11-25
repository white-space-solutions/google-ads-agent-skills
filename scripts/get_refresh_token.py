"""Generate a Google Ads API refresh token (one time). Reads GOOGLE_ADS_CLIENT_ID and
GOOGLE_ADS_CLIENT_SECRET from .env, opens a browser to approve, writes the token back to .env.

  python scripts/get_refresh_token.py
"""
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

ENV = Path(os.environ.get("GOOGLE_ADS_ENV", Path(__file__).resolve().parent.parent / ".env")).expanduser()
if not ENV.exists():
    raise SystemExit(f"{ENV} not found. Copy .env.example to .env and add your OAuth client ID and secret first.")
load_dotenv(ENV)
cid, secret = os.getenv("GOOGLE_ADS_CLIENT_ID", "").strip(), os.getenv("GOOGLE_ADS_CLIENT_SECRET", "").strip()
if not cid or not secret:
    raise SystemExit("GOOGLE_ADS_CLIENT_ID / GOOGLE_ADS_CLIENT_SECRET missing from .env")
flow = InstalledAppFlow.from_client_config({"installed": {
    "client_id": cid, "client_secret": secret, "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token", "redirect_uris": ["http://localhost"]}},
    ["https://www.googleapis.com/auth/adwords"])
creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
text = ENV.read_text()
if re.search(r"^GOOGLE_ADS_REFRESH_TOKEN=", text, flags=re.M):
    text = re.sub(r"^GOOGLE_ADS_REFRESH_TOKEN=.*$", f"GOOGLE_ADS_REFRESH_TOKEN={creds.refresh_token}", text, flags=re.M)
else:
    text += f"\nGOOGLE_ADS_REFRESH_TOKEN={creds.refresh_token}\n"
ENV.write_text(text)
print("Refresh token saved to", ENV)
