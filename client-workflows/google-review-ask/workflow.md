# Workflow: Google review-ask

**Offering:** help a client collect more Google reviews with a ready-to-send ask after each job.
**Reusable across all tenants.** First built 2026-07-05 (G&K/Kim). Improve this file each time it runs.

## Trigger
Client mentions Google/Facebook reviews, OR the agent offers a review-ask and the client accepts.
On acceptance → open a matter `office/matters/google-review-ask-<date>.md` (status: open).

## HARD RULE — never touch the client's Google Business Profile
Autonomous agents must NEVER log into, scrape, or modify a client's GBP / Google Maps / Google
account (suspension/ban/identity risk — `feedback_never_touch_google_business_profiles`). We get the
review link FROM the client. Our job is to make that effortless for them.

## Steps
1. **Get the review URL from the client.** Text them (plain, one step):
   > "On your phone, open Google and search your business name → tap your Business Profile → tap
   > **'Ask for reviews'** (or 'Get more reviews') → copy the short link (looks like `g.page/r/…`)
   > and text it back to me. That's the exact link customers use to leave a review."
   Save the returned link to the client's business file. If they can't find it, offer the fallback:
   they can also get it from Google Business Profile → Home → "Get more reviews" → Share.
2. **Draft the review-ask message** the client sends right after a job (short, warm, their voice):
   > "Thanks again for trusting [Business] with your project! If you have 30 seconds, a quick Google
   > review really helps us out: [review link]. We appreciate you!"
   Save it as a reusable template in the client's workspace.
3. **(Optional, if client wants) automate:** wire the agent to send the ask per completed job.
4. **Close the matter** when: review link on file + ask template saved (+ automation if requested).

## Done-definition
Client has their Google review link saved AND a ready-to-send review-ask template.

## Improvement log (append each run — this is how the workflow gets better)
- 2026-07-05 (G&K/Kim, first build): established the never-touch-GBP → client-self-serve-instructions
  pattern + the ask template. TODO next run: A/B a couple ask-message variants; add the per-job
  automation option; consider a QR-code version of the review link for job-site signage.
