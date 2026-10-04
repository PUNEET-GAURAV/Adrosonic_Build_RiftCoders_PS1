import os

path = "src/trustrag/retrieval/orchestrator.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Add always-on filters
target = """        if groups and request.filters.acl_groups is None:
            # permission-aware retrieval: the caller's groups become a pre-retrieval filter
            request.filters.acl_groups = list(groups)
            
        # -- ROUTING INJECTION --"""

replacement = """        if groups and request.filters.acl_groups is None:
            # permission-aware retrieval: the caller's groups become a pre-retrieval filter
            request.filters.acl_groups = list(groups)
            
        # ALWAYS-ON BANKING FILTERS
        if getattr(request, "session", None):
            if "tenant" in request.session and getattr(request.filters, "tenant", None) is None:
                setattr(request.filters, "tenant", request.session["tenant"])
            if "audience" in request.session and getattr(request.filters, "audience", None) is None:
                setattr(request.filters, "audience", request.session["audience"])
        if getattr(request.filters, "superseded", None) is None and getattr(request, "as_of", None) is None:
            setattr(request.filters, "superseded", False)
            
        # -- ROUTING INJECTION --"""

text = text.replace(target, replacement)
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("Patched orchestrator!")
