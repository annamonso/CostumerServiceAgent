# Escalation Rules

## When to Escalate Immediately

Escalate the ticket **without delay** if any of the following triggers are detected in the customer's message or account data:

### Legal / Fraud Triggers (Priority: HIGH)
Escalate with `priority: "high"` if the customer mentions or implies:
- "lawyer" or "attorney"
- "legal action" or "lawsuit"
- "fraud" or "fraudulent charge"
- "chargeback" or "dispute with my bank"
- "report to the BBB" or "consumer protection"
- Any claim of identity theft or unauthorized account access

**Action:** Use `escalate_ticket(customer_id, reason, priority="high")` immediately. Do not attempt to resolve the issue yourself. Inform the customer that a senior specialist will contact them within 15 minutes.

### Enterprise / VIP Customers (Priority: MEDIUM)
Escalate with `priority: "medium"` if:
- The customer's plan is `enterprise`.
- Always provide VIP-level treatment; do not leave an enterprise customer waiting on a standard resolution path.

**Action:** Use `escalate_ticket(customer_id, reason, priority="medium")`. Assure the customer that a dedicated account manager will follow up within 2 hours. You may still resolve straightforward issues (refunds, order lookups) in parallel before escalating.

### Repeated Failed Resolutions (Priority: NORMAL)
Escalate with `priority: "normal"` if:
- The customer's ticket history shows 3 or more previously resolved tickets for the same or similar issue.
- The current interaction involves a second or subsequent contact about the same unresolved problem.

**Action:** Use `escalate_ticket` to ensure a human reviews the pattern and provides a lasting resolution.

### Abusive or Threatening Behavior (Priority: HIGH)
Escalate with `priority: "high"` if the customer:
- Uses threatening or abusive language directed at staff or the company.
- Makes personal threats.

**Action:** De-escalate calmly, do not engage with the hostility, and immediately escalate. Inform the customer that a specialist will be in touch.

### Account Security Breach (Priority: HIGH)
Escalate with `priority: "high"` if:
- The customer reports unauthorized orders, logins, or password changes.
- Account status is `suspended` due to suspected fraudulent activity.

**Action:** Advise the customer to use the "Secure My Account" feature immediately. Escalate to the security team with full context.

## How to Escalate

1. Call `get_customer(email)` to confirm `customer_id` and plan tier.
2. Call `escalate_ticket(customer_id, reason, priority)` where:
   - `reason` is a clear, brief description of the issue (e.g., "Customer mentioned potential chargeback on order ORD-1003").
   - `priority` follows the rules above.
3. Communicate the escalation outcome to the customer:
   - Provide the escalation ticket ID from the tool response.
   - State the expected response time.
   - Reassure the customer that their issue is being taken seriously.
4. Do **not** make promises about specific outcomes that you cannot guarantee (e.g., "you will get a full refund" — unless the refund policy guarantees it).
