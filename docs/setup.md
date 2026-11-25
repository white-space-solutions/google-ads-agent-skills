# Google Ads API setup

**Goal:** let your AI agent (Claude Code, Cowork, Codex, a Grok bot, or any agent that can run Python) read your Google Ads account and, with your approval, change it through the official API. No Sheets, no CSV exports.

**Time:** about 20 minutes of clicks, then a 1 to 2 business day wait for Google to approve the developer token.

**End state:** a `.env` file with four secrets in the repo root (never committed) and a client file (`clients/<name>.yaml`) with the account IDs.

**Already have API access?** If you or your agency already has a developer token and an OAuth client, do Steps 2, 7 and 8 for each new account.

---

## What you end up with

`.env` (secrets, copied from `.env.example`):

```
GOOGLE_ADS_DEVELOPER_TOKEN=ABcdeFGHij1234567890
GOOGLE_ADS_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
GOOGLE_ADS_REFRESH_TOKEN=1//xxxxxxxxxxxxxxxxxx
```

`clients/<name>.yaml` (not secret, copied from `clients/example.yaml`):

```yaml
customer_id: "987-654-3210"        # the ad account
login_customer_id: "123-456-7890"  # your manager (MCC) ID, or the ad account itself (see Step 8)
```

---

## Step 1: Create a manager account (MCC)

Google issues developer tokens to manager accounts, not to regular ad accounts.

1. Go to https://ads.google.com/home/tools/manager-accounts/ and click **Create a manager account**.
2. Name it after your business. Pick your country, time zone and currency.
3. After it is created, find the **Customer ID** in the top-right corner of the manager account (format `123-456-7890`).

Every Google Ads account has its own Customer ID. You will use two: the **manager** ID (for `login_customer_id`) and the **ad account** ID (for `customer_id`). Do not mix them up.

## Step 2: Link the ad account to the manager

1. In the manager account: **Accounts > Sub-account settings > Link existing account**.
2. Enter the ad account's Customer ID and send the request.
3. Accept it from the ad account: the invitation arrives by email, and also appears under the bell icon in the ad account. You must be signed in as an admin of the ad account to accept.

Agencies often skip this: if the client added your Google user to their ad account directly, you can use direct access instead (Step 8 explains).

## Step 3: Apply for a developer token

1. In the **manager** account: **Admin > API Center** (search "API Center" if you cannot find it).
2. Fill in the form. Keep three things consistent: your contact email's domain, the company URL, and the company name. Mismatches are the most common reason for rejection.
3. Company type: **Advertiser** if you manage your own business's ads. **Agency** if you manage client accounts.
4. Intended use: describe what the tool does in plain terms. For example:

   ```
   Internal tool to manage Google Ads accounts we own or manage. It reads reporting data (campaigns,
   keywords, search terms, conversions) through GoogleAdsService.search, produces recommendations,
   and applies negative keyword and keyword changes only after a person on our team approves them.
   No external users, no resale.
   ```

5. Submit. You immediately get a token string in **Test** access (it works only on test accounts). Save it as `GOOGLE_ADS_DEVELOPER_TOKEN` in `.env` now.
6. Click **Apply for Basic Access**. That form asks for a short design document (PDF): company name, business model, who uses the tool (internal only), how data flows in and out, which API services you call, and one wireframe screenshot. Keep it short and factual. Do not oversell; describe what the tool actually does.
7. Google reviews it in 1 to 2 business days. When approved, the same token starts working on real accounts. Nothing else changes.

## Step 4: Create a Google Cloud project

1. Go to https://console.cloud.google.com, create a project (any name).
2. Search for **Google Ads API** and click **Enable**.

## Step 5: Configure the OAuth consent screen

1. **APIs & Services > OAuth consent screen**. User type: **External**.
2. Fill in the app name and your email. Skip logo and scopes.
3. Under **Test users**, add the Google account that has access to the ad account or manager.
4. Leave it in Testing mode. That is fine for your own use.

## Step 6: Create OAuth credentials

1. **APIs & Services > Credentials > Create credentials > OAuth client ID**.
2. Application type: **Desktop app**. Create.
3. Copy the client ID and client secret into `.env` as `GOOGLE_ADS_CLIENT_ID` and `GOOGLE_ADS_CLIENT_SECRET`.

## Step 7: Generate the refresh token

1. Install dependencies: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. Run `.venv/bin/python scripts/get_refresh_token.py`
3. A browser opens. Sign in with the Google account that has access to the ad account (or the manager). Click through the "Google hasn't verified this app" screen; it is your own app.
4. The script writes `GOOGLE_ADS_REFRESH_TOKEN` into `.env`.

## Step 8: Verify

1. Copy `clients/example.yaml` to `clients/<name>.yaml` and set `customer_id` and `login_customer_id`.
2. Run `.venv/bin/python scripts/check_connection.py --client clients/<name>.yaml`

It lists every account your credentials can reach, then tries the ad account with your `login_customer_id` and, if that fails, with the ad account's own ID. It tells you which one to use.

**Manager vs direct access.** Through a manager link, `login_customer_id` is the manager ID. If your Google user was added to the ad account directly, `login_customer_id` is the ad account's own ID, and going through the manager can fail.

### Access levels

| Level | What it means |
|---|---|
| Test | Works only on test accounts. Real calls fail with "not approved". |
| Explorer | Real accounts with a low daily operations quota. Reads are fine; a large negative keyword rebuild can hit the write quota. Finish in the UI or the next day. |
| Basic | Real accounts, 15,000 operations a day. Enough for most agencies. |
| Standard | Unlimited operations. Apply when you outgrow Basic. |

---

## Common errors

| Error | Fix |
|---|---|
| `Developer token is not approved` | Still in Test access. Wait for the approval email. |
| `invalid_grant` | The refresh token was revoked or mistyped. Run Step 7 again. |
| `USER_PERMISSION_DENIED` or login customer errors | Wrong `login_customer_id`. Run `check_connection.py`; it tells you which ID works. |
| `CUSTOMER_NOT_FOUND` or not authorized | The link in Step 2 was not accepted, or your Google user has no access to the account. |
| Worked before, now `403` | The refresh token expired (OAuth apps in Testing mode issue tokens that can expire). Run Step 7 again. |

## Security

- Never commit `.env`. It is in `.gitignore`; keep it there.
- The refresh token is a master key to every account your Google user can reach. Treat it like a password.
- If you think it leaked: revoke the app at https://myaccount.google.com/permissions and run Step 7 again.
- Give the agent only what it needs. Audits are read-only, and every write script in this repo is a dry run until a person approves it.
