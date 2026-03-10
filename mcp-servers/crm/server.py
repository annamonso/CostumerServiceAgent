from mcp.server.fastmcp import FastMCP
import json
import pathlib

mcp = FastMCP("crm", host="0.0.0.0", port=8002, streamable_http_path="/mcp")
DATA = pathlib.Path(__file__).parent / "data"


@mcp.tool()
def get_customer(email: str) -> dict:
    """Look up a customer by email address."""
    customers = json.loads((DATA / "customers.json").read_text())
    for c in customers:
        if c["email"].lower() == email.lower():
            return c
    return {"error": f"No customer found with email {email}"}


@mcp.tool()
def get_order(order_id: str) -> dict:
    """Look up an order by order ID."""
    orders = json.loads((DATA / "orders.json").read_text())
    for o in orders:
        if o["order_id"] == order_id:
            return o
    return {"error": f"No order found with ID {order_id}"}


@mcp.tool()
def get_orders_by_customer(customer_id: str) -> list[dict]:
    """Get all orders for a customer by their customer ID."""
    orders = json.loads((DATA / "orders.json").read_text())
    results = [o for o in orders if o["customer_id"] == customer_id]
    return results if results else [{"message": f"No orders found for customer {customer_id}"}]


@mcp.tool()
def get_ticket_history(customer_id: str) -> list[dict]:
    """Get past support ticket history for a customer."""
    tickets = [
        {
            "ticket_id": "T001",
            "customer_id": "C001",
            "issue": "Late delivery",
            "status": "resolved",
            "resolution": "Refund issued",
            "date": "2024-11-15",
        },
        {
            "ticket_id": "T002",
            "customer_id": "C003",
            "issue": "Wrong item shipped",
            "status": "resolved",
            "resolution": "Replacement sent",
            "date": "2024-12-01",
        },
        {
            "ticket_id": "T003",
            "customer_id": "C007",
            "issue": "Account login issue",
            "status": "resolved",
            "resolution": "Password reset",
            "date": "2025-01-10",
        },
    ]
    results = [t for t in tickets if t["customer_id"] == customer_id]
    return results if results else [{"message": "No previous tickets found"}]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
