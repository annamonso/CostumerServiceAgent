# Refund Policy

## Overview
ShopEasy is committed to customer satisfaction. Use this policy to determine the correct refund action for any given situation.

## Refund Eligibility Rules

### Full Refund (100%)
Issue a full refund when **any** of the following conditions are met:
- The item was never delivered (status remains `in_transit` or `processing` beyond the estimated delivery window of 10 business days).
- The item arrived significantly not as described (wrong product, major undisclosed defect, or damaged beyond use).
- The customer is on the **Enterprise plan** — Enterprise customers always receive a full refund, no questions asked.

### Partial Refund (50%)
Issue a 50% partial refund when:
- The item has been opened but is being returned within **14 days** of delivery.
- The item shows minor use but is otherwise in acceptable condition.
- Note: The partial refund covers the item cost only; original shipping is non-refundable.

### No Refund
Do **not** issue a refund when:
- More than **30 days** have elapsed since the delivery date, unless the item is confirmed defective under warranty.
- The item is a **digital product** (software license, digital download) that has already been activated or downloaded.
- The item is marked as non-returnable (custom/personalized items, perishables, intimate apparel).
- The order status is `cancelled` — these do not generate a charge and therefore no refund is needed.

### Defective Items (Exception to 30-Day Rule)
If a customer reports a defective item and provides credible evidence (photo, description):
- Within 1 year of purchase: issue a full refund or replacement, regardless of the 30-day window.
- Beyond 1 year: advise the customer to pursue a warranty claim through ShopEasy Shield or the manufacturer.

## Instructions for Claude

1. **Always look up the order first.** Use `get_order(order_id)` to verify the order status, delivery date, and `eligible_for_refund` flag before deciding.
2. **Check the customer's plan.** Use `get_customer(email)` to confirm if the customer is on an Enterprise plan — Enterprise customers always get a full refund.
3. **Calculate days since delivery.** Compare `delivery_date` to today's date. Apply the appropriate rule (full / partial / none).
4. **Check `eligible_for_refund`.** If the flag is `false` and the situation does not fall under an exception (Enterprise, defective), do not issue a refund without escalating first.
5. **Use `issue_refund(order_id, reason)`** only after determining eligibility. Always state the reason clearly (e.g., "Item not delivered", "Enterprise customer — automatic full refund", "Defective product reported within warranty period").
6. **Communicate clearly.** Tell the customer the refund amount, the timeline (5–10 business days), and the refund destination (original payment method).
7. **When in doubt, escalate** using `escalate_ticket` rather than denying or issuing an incorrect refund.
