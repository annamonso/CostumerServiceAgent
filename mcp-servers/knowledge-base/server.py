from mcp.server.fastmcp import FastMCP
import json
import pathlib

mcp = FastMCP("knowledge-base", host="0.0.0.0", port=8001, streamable_http_path="/mcp")
DATA = pathlib.Path(__file__).parent / "data"


@mcp.tool()
def search_faqs(query: str) -> list[dict]:
    """Search the FAQ knowledge base for answers to customer questions."""
    faqs = json.loads((DATA / "faqs.json").read_text())
    q = query.lower()
    return [
        f for f in faqs
        if q in f["question"].lower()
        or q in f["answer"].lower()
        or q in f.get("category", "").lower()
    ]


@mcp.tool()
def search_docs(topic: str) -> list[dict]:
    """Search documentation by topic."""
    docs = json.loads((DATA / "docs.json").read_text())
    t = topic.lower()
    return [
        d for d in docs
        if t in d["topic"].lower()
        or t in d["title"].lower()
        or t in d["content"].lower()
    ]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
