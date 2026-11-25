# Conversion setup for home buyers and wholesalers

The playbook rule is "measure qualified leads, not form fills". This is how to do that for a seller-lead business. See `docs/playbook/02-conversion-tracking.md` for the general rules.

## 1. Define the stages

Write these down and agree on them with whoever works the leads. Use your CRM's own status names.

| Stage | Definition (adapt) | Google Ads action | Primary? |
|---|---|---|---|
| Lead | Form submit or a call over 60 seconds | Lead (website form) and calls | Primary at launch |
| Qualified lead | Owner of the property, in your buy box, motivated, willing to talk price | Qualified Lead (offline upload) | Primary once volume allows |
| Appointment | Walkthrough or offer call booked | Appointment (offline upload) | Secondary |
| Contract | Signed purchase agreement | Under Contract (offline upload) | Secondary |
| Closed | Deal closed or assigned | Closed (offline upload) | Secondary |

Secondary actions are still reported, so you can see cost per appointment and per contract, but bidding does not chase them.

## 2. Set stage values from your numbers

Value of a stage = (share of that stage that becomes a closed deal) x (average profit or assignment fee per deal).

Worked example (replace with your own last 6 to 12 months):

| | Your number |
|---|---|
| Average assignment fee or profit per deal | $15,000 |
| Qualified lead to closed deal | 8% |
| Appointment to closed deal | 25% |
| Contract to closed deal | 70% |

| Stage | Value |
|---|---|
| Qualified lead | $15,000 x 8% = $1,200 |
| Appointment | $15,000 x 25% = $3,750 |
| Contract | $15,000 x 70% = $10,500 |

Write the values down with the date and the numbers behind them. Change them at most once a quarter. Every change makes value-based bidding re-learn.

## 3. Send CRM outcomes back to Google

The click ID has to travel with the lead:

1. **Auto-tagging on** in Google Ads (adds `gclid` to every ad click).
2. **The landing page form stores** `gclid`, `gbraid`/`wbraid`, UTM source/medium/campaign/term and the page or variant in hidden fields.
3. **The CRM keeps those fields** on the lead record (Podio, REsimpli, InvestorFuse, GoHighLevel, Salesforce and others all support custom fields).
4. **When the lead changes stage**, send an offline conversion upload: the click ID, the conversion action name, the time of the stage change and the value. Options:
   - Google Ads Data Manager or a native CRM integration, where your CRM has one.
   - Zapier, Make or n8n: "lead status changed" trigger, "Google Ads: upload offline conversion" action.
   - A script against the Google Ads API (`ConversionUploadService`).
5. **Turn on enhanced conversions for leads** and send hashed email and phone too. It recovers matches when the click ID is lost.

Rules that save you later:

- **One pipeline per conversion action.** Never two tools uploading "Qualified Lead".
- **Upload within a day** of the stage change, and inside the action's lookback window (set it to 60 to 90 days; seller leads qualify slowly).
- **Check uploads daily** (`scripts/conversion_health.py`): failures are silent otherwise.

## 4. Calls

Most seller leads call. Count them once:

- Use **one** call-tracking source for website calls (Google forwarding numbers, CallRail, or your phone system's integration), and the call asset for calls from the ad itself.
- Count a call as a lead only above a duration threshold (60 to 90 seconds) to skip wrong numbers and solicitors.
- Make sure calls create CRM leads with the click ID or tracking number attached, so they can be qualified and uploaded like forms.
- Do not keep three overlapping call actions all counting as primary.

## 5. Test it end to end before launch

1. Click your own ad, or open the landing page with `?gclid=TEST-123` in the URL.
2. Submit the form. Confirm the CRM record has the click ID and UTMs.
3. Move the test lead to "qualified" and confirm the upload fires (it will be rejected by Google for a fake click ID, which proves the pipe works). Delete the test lead.
4. Place a test call and confirm it lands in the CRM with its source.
