import os

path = "docs/architecture.md"
with open(path, "a", encoding="utf-8") as f:
    f.write("\n## Banking Intent Router\n\n```mermaid\nflowchart TB\n  Q[User Query] --> R[Lexical Intent Router]\n  R -->|High Confidence| H[Hard Strategy: Filter to domain]\n  R -->|Medium Confidence| S[Soft Strategy: Filter to top 2 domains]\n  R -->|Low Confidence| F[Fallback: Global Hybrid Search + Needs Clarification]\n  H --> Qdrant\n  S --> Qdrant\n  F --> Qdrant\n```\n")
print("Updated architecture.md")
