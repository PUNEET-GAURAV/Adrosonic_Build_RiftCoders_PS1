from typing import Protocol, Any
from pydantic import BaseModel, Field
import time
import numpy as np
import yaml

class RouteResult(BaseModel):
    strategy: str = "off"
    domain: str | None = None
    topic: str | None = None
    confidence: float = 0.0
    margin: float = 0.0
    alternatives: list[str] = Field(default_factory=list)
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    expanded_terms: list[str] = Field(default_factory=list)
    search_space_ratio: float | None = None
    retries: int = 0
    router_ms: float = 0.0
    needs_clarification: bool = False
    clarification_options: list[str] = Field(default_factory=list)

class Router(Protocol):
    def route(self, query: str, dense_vec: list[float] | None = None) -> RouteResult:
        ...

class NoRouter:
    def route(self, query: str, dense_vec: list[float] | None = None) -> RouteResult:
        return RouteResult()

class LexicalRouter:
    def __init__(self, taxonomy_path: str = "configs/banking_taxonomy.yaml"):
        with open(taxonomy_path, "r") as f:
            self.taxonomy = yaml.safe_load(f)["domains"]
            
        self.domain_keywords = {}
        for dom, data in self.taxonomy.items():
            # Lowercase all keywords
            self.domain_keywords[dom] = [k.lower() for k in data["keywords"]]

    def route(self, query: str, dense_vec: list[float] | None = None) -> RouteResult:
        t0 = time.perf_counter()
        q_lower = query.lower()
        
        scores = {}
        for dom, keywords in self.domain_keywords.items():
            score = sum(1 for k in keywords if k in q_lower)
            scores[dom] = score
            
        # Fast rule: if no keywords match, fallback
        if not any(scores.values()):
            return RouteResult(
                strategy="fallback",
                confidence=0.0,
                router_ms=round((time.perf_counter() - t0) * 1000, 2),
                needs_clarification=True,
                clarification_options=list(self.taxonomy.keys())[:3] # Suggest top 3 generic
            )
            
        # Sort domains by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_dom, top_score = ranked[0]
        runner_up_score = ranked[1][1] if len(ranked) > 1 else 0
        
        confidence = min(top_score / 2.0, 1.0) # Normalise pseudo-confidence
        margin = (top_score - runner_up_score) / 2.0
        
        res = RouteResult(
            strategy="hard" if margin >= 0.5 else "soft",
            domain=top_dom,
            confidence=confidence,
            margin=margin,
            filters_applied={"domain": [top_dom]} if margin >= 0.5 else {"domain": [ranked[0][0], ranked[1][0]]}
        )
        
        if res.strategy == "soft":
            res.alternatives = [ranked[1][0]]
            res.needs_clarification = True
            res.clarification_options = [ranked[0][0], ranked[1][0]]
            
        res.router_ms = round((time.perf_counter() - t0) * 1000, 2)
        return res
