# TrustRAG Hackathon Report

## 1. Executive Summary
TrustRAG was augmented to support a **Banking Knowledge Vertical** utilizing a highly resilient and blazingly fast Intent Router ("Verity Router"). This fulfills the challenge requirement for Vector Database Design for RAG System.

## 2. Banking Vertical: Intent-Aware Domain Routing
A naive RAG pipeline searches the entire vector space for every query. This is computationally expensive and prone to cross-domain hallucinations (e.g. retrieving KYC documents for fixed deposits when the user asked about loans).

### 2.1 The Solution
We implemented a config-driven **Lexical Intent Router** (`src/trustrag/routing/router.py`) combined with pre-retrieval Qdrant payload filtering.
- **Speed**: The router executes in ~0.04ms on CPU.
- **Fail-Safe Design**: If routing results in too few passages (e.g., due to over-filtering), the Orchestrator instantly strips the filter, logs the retry, and executes a global hybrid search. The user never sees an error.
- **Ambiguity Handling**: Generic queries like *"What documents are needed?"* bypass filtering entirely but prompt the UI to show Clarification Chips ("Did you mean: kyc_onboarding or loans?").

### 2.2 Measured Evidence
Evaluated on 121 synthetically generated queries over 500 documents spanning 8 distinct banking domains (see `results/banking_eval_metrics.json`):

*   **Routing Accuracy**: **82.1%** correct top-1 domain match.
*   **Search Space Reduction**: The router reduced the average retrieval search space to just **15.1%** of the total index.
*   **Latency Win**: Filtering via routing reduced overall end-to-end p50 retrieval latency from **33.62ms** to **29.91ms**.
*   **Safety**: Clarified 9/10 intentionally ambiguous queries and successfully abstained/fell back on 5/5 out-of-scope queries.

## 3. Limitations
*   The evaluation corpus is strictly synthetic due to hackathon data privacy requirements. No real customer data was indexed.
*   Lexical routing requires careful taxonomy configuration. It trades off deep semantic intent understanding for a guarantee of <1ms execution latency, keeping us strictly within our hackathon SLA constraints.
