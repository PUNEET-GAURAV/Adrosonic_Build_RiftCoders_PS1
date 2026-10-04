import json
import random
import uuid
import itertools
from datetime import datetime
from trustrag.core.models import Passage
from trustrag.adapters.st_embedder import SentenceTransformerEmbedder
from trustrag.adapters.bm25_sparse import BM25SparseEncoder
from trustrag.adapters.qdrant_store import QdrantStore
from trustrag.ingestion.pipeline import ingest_corpus

DOMAINS = [
    "kyc_onboarding", "savings_current_accounts", "loans", "fixed_deposits", 
    "insurance_bancassurance", "cards", "payments_transfers", "grievance_complaints"
]

TOPICS = ["document_requirements", "eligibility", "process_steps", "fees_charges", "timelines"]
AUDIENCES = ["individual", "business", "any"]
TENANTS = ["bank_A", "bank_B"]

TEMPLATES = {
    "kyc_onboarding": [
        "To open a {audience} account, you must provide valid KYC documents including {doc1} and {doc2}.",
        "The {topic} for {domain} mandate that a proof of identity such as {doc1} is submitted.",
        "Account opening is fast. Simply provide {doc1} for identity verification."
    ],
    "loans": [
        "For a home loan, the required documents are {doc1} and {doc2}.",
        "Loan {topic} depends on your credit score and providing {doc1} as proof of income.",
        "To secure your loan, ensure your {doc1} and {doc2} are verified by the bank."
    ],
    "fixed_deposits": [
        "Opening a fixed deposit requires {doc1} if you are a new customer.",
        "The interest rate for FDs is fixed at maturity. The {topic} are provided in your receipt.",
        "Premature withdrawal of FDs may incur a penalty of 1% on the total value."
    ],
    "cards": [
        "To apply for a new credit card, submit your {doc1} along with your application.",
        "Your credit card billing cycle is 30 days. Late fees apply if you miss the {topic}.",
        "Reward points on your card can be redeemed for flights or cashback."
    ],
    "savings_current_accounts": [
        "Savings accounts require a minimum balance of $500. Current accounts have no limit.",
        "Overdraft facilities are available for current accounts. See {topic} for details.",
        "Interest on savings accounts is calculated daily and credited quarterly."
    ],
    "insurance_bancassurance": [
        "Life insurance policies offer a grace period of 30 days for premium payment.",
        "Health insurance claims must be filed within 90 days. Check the {topic}.",
        "Your bancassurance policy covers accidental death and permanent disability."
    ],
    "payments_transfers": [
        "NEFT transfers are processed in batches every half hour.",
        "For international SWIFT transfers, the fee is flat $15. See {topic} for daily limits.",
        "IMPS allows instant funds transfer 24/7 up to $2000."
    ],
    "grievance_complaints": [
        "If you are unsatisfied, register a complaint online. Our response {topic} is 48 hours.",
        "You may escalate disputes to the Banking Ombudsman if unresolved within 30 days.",
        "For customer support, call our toll-free number or visit your nearest branch."
    ]
}

DOCS = ["passport", "driving license", "pan card", "utility bill", "salary slip", "tax return"]

def generate_passages(n=500):
    passages = []
    for i in range(n):
        domain = random.choice(DOMAINS)
        topic = random.choice(TOPICS)
        audience = random.choice(AUDIENCES)
        tenant = random.choice(TENANTS)
        superseded = random.random() < 0.1 # 10% superseded
        doc1, doc2 = random.sample(DOCS, 2)
        
        template = random.choice(TEMPLATES[domain])
        text = template.format(audience=audience, doc1=doc1, doc2=doc2, topic=topic, domain=domain.replace("_", " "))
        
        # Add random variations to avoid exact duplicates
        text += f" [Ref: {uuid.uuid4().hex[:8]}]"
        
        p = Passage(
            passage_id=str(uuid.uuid4()),
            text=text,
            source="synthetic_banking",
            category="banking",
            topic=topic,
            domain=domain,
            audience=audience,
            tenant=tenant,
            superseded=superseded,
            label_origin="synthetic"
        )
        passages.append(p)
    return passages

def main():
    print("Generating synthetic banking passages...")
    passages = generate_passages(500)
    
    # Save for reference
    with open("data/banking/synthetic_corpus.jsonl", "w") as f:
        for p in passages:
            f.write(p.model_dump_json() + "\n")
            
    print("Saved to data/banking/synthetic_corpus.jsonl")
    
    # Ingest directly
    print("Ingesting to Qdrant (passages)...")
    store = QdrantStore("http://localhost:6333", collection="passages")
    embedder = SentenceTransformerEmbedder("BAAI/bge-small-en-v1.5", query_prefix="Represent this sentence for searching relevant passages: ")
    sparse = BM25SparseEncoder(hash_bits=32)
    
    # Batch size
    batch_size = 64
    for i in range(0, len(passages), batch_size):
        batch = passages[i:i+batch_size]
        texts = [p.text for p in batch]
        dense_vecs = embedder.embed_documents(texts)
        sparse_vecs = sparse.encode_documents(texts)
        store.upsert(batch, dense_vecs, sparse_vecs)
        print(f"Upserted batch {i} to {i+len(batch)}...")
        
    print("Ingest complete!")

if __name__ == "__main__":
    main()
