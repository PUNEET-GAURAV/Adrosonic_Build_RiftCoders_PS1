import json
import random

TAXONOMY = {
    "kyc_onboarding": {
        "keywords": ["kyc", "onboarding", "account opening", "identity proof", "address proof", "documents", "passport", "pan card"]
    },
    "savings_current_accounts": {
        "keywords": ["savings", "current account", "minimum balance", "interest rate", "cheque book", "overdraft"]
    },
    "loans": {
        "keywords": ["loan", "emi", "interest rate", "mortgage", "collateral", "home loan", "personal loan", "cibil"]
    },
    "fixed_deposits": {
        "keywords": ["fd", "fixed deposit", "maturity", "premature withdrawal", "penalty", "recurring deposit", "rd", "interest"]
    },
    "insurance_bancassurance": {
        "keywords": ["insurance", "premium", "policy", "claim", "coverage", "nominee", "term life", "health insurance"]
    },
    "cards": {
        "keywords": ["credit card", "debit card", "pin", "cvv", "limit", "reward points", "annual fee", "lounge access", "forex card"]
    },
    "payments_transfers": {
        "keywords": ["neft", "rtgs", "imps", "upi", "swift", "transfer", "remittance", "beneficiary", "transaction limit"]
    },
    "grievance_complaints": {
        "keywords": ["complaint", "grievance", "dispute", "ombudsman", "fraud", "chargeback", "customer care", "helpline"]
    }
}

templates = [
    "What are the {kw} requirements for {domain}?",
    "How do I apply for a {kw} in {domain}?",
    "Tell me about {domain} {kw} policies.",
    "Is {kw} mandatory for {domain}?",
    "Can you explain {kw} for {domain}?",
    "What happens to my {kw} if I close my {domain}?",
    "Are there hidden fees for {kw} in {domain}?",
    "I need help with my {domain} {kw}.",
    "Where can I find the form for {domain} {kw}?",
    "What is the limit on {kw} in {domain}?",
]

queries = []

# Generate explicit domain queries
for domain, data in TAXONOMY.items():
    for _ in range(12):
        kw = random.choice(data["keywords"])
        q = random.choice(templates).format(kw=kw, domain=domain.replace('_', ' '))
        queries.append({
            "query": q,
            "expected_domain": domain,
            "type": "explicit"
        })

# Generate ambiguous queries
ambiguous = [
    "What documents are needed?",
    "How long does the process take?",
    "What is the interest rate?",
    "Can I cancel it?",
    "Where is the branch?",
    "What are the fees?",
    "Is this available for NRIs?",
    "Do I need to visit the branch?",
    "Can I do this online?",
    "How to check my status?"
]
for q in ambiguous:
    queries.append({
        "query": q,
        "expected_domain": None,
        "type": "ambiguous"
    })

# Out of scope queries
oos = [
    "What's the weather today?",
    "Who won the match?",
    "Recipe for pasta",
    "How to fix a flat tire",
    "Best movies of 2023"
]
for q in oos:
    queries.append({
        "query": q,
        "expected_domain": None,
        "type": "out_of_scope"
    })

import os
os.makedirs("data/banking", exist_ok=True)
with open("data/banking/eval_queries.jsonl", "w") as f:
    for q in queries:
        f.write(json.dumps(q) + "\n")

print(f"Generated {len(queries)} queries.")
