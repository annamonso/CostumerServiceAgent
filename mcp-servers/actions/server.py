from mcp.server.fastmcp import FastMCP
import uuid
from datetime import datetime, timezone

mcp = FastMCP("actions", host="0.0.0.0", port=8003, streamable_http_path="/mcp")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@mcp.tool()
def issue_refund(order_id: str, reason: str) -> dict:
    """Issue a refund for an order. Returns a confirmation with refund ID and timestamp."""
    refund_id = f"REF-{uuid.uuid4().hex[:8].upper()}"
    return {
        "success": True,
        "refund_id": refund_id,
        "order_id": order_id,
        "reason": reason,
        "status": "approved",
        "message": f"Refund {refund_id} has been issued for order {order_id}. "
                   f"Funds will be returned to the original payment method within 5-10 business days.",
        "timestamp": _now(),
    }


@mcp.tool()
def escalate_ticket(customer_id: str, reason: str, priority: str) -> dict:
    """Escalate a support ticket to a human agent. Priority must be 'high', 'medium', or 'normal'."""
    valid_priorities = {"high", "medium", "normal"}
    if priority not in valid_priorities:
        priority = "normal"

    ticket_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    eta_map = {"high": "15 minutes", "medium": "2 hours", "normal": "24 hours"}
    return {
        "success": True,
        "escalation_id": ticket_id,
        "customer_id": customer_id,
        "priority": priority,
        "reason": reason,
        "assigned_team": "Tier-2 Support" if priority == "normal" else "Senior Support",
        "estimated_response": eta_map[priority],
        "message": f"Ticket {ticket_id} has been escalated with {priority} priority. "
                   f"A specialist will reach out within {eta_map[priority]}.",
        "timestamp": _now(),
    }


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email to a customer. Returns a delivery confirmation."""
    message_id = f"MSG-{uuid.uuid4().hex[:10].upper()}"
    return {
        "success": True,
        "message_id": message_id,
        "to": to,
        "subject": subject,
        "status": "sent",
        "message": f"Email successfully sent to {to} with subject '{subject}'.",
        "timestamp": _now(),
    }


@mcp.tool()
def create_ticket(customer_id: str, issue: str, category: str) -> dict:
    """Create a new support ticket for a customer."""
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    return {
        "success": True,
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "category": category,
        "status": "open",
        "message": f"Support ticket {ticket_id} has been created and assigned to the {category} team. "
                   f"You will receive a confirmation email shortly.",
        "timestamp": _now(),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
