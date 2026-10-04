# Verity Banking Corpus

This directory contains the synthetic banking dataset created for the Hackathon.

## Data Generation
**Method:** Combinatorial string templating using 8 core banking domains, 5 document types, 5 intents, and random UUID permutations.
**Seed / Origin:** `scripts/generate_banking_corpus.py` (Script generated via LLM, but no LLM was used for the content extraction loop to ensure 100% deterministic success without rate-limits).
**Total Passages:** 500
**Synthetic Label:** All passages have `label_origin: synthetic` and `synthetic: true`.

## Collections
The data is stored in the `verity_banking` Qdrant collection, completely isolated from the standard MS MARCO collection used for baseline evaluation.
