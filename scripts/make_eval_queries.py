import json
import pandas as pd
from pathlib import Path

df = pd.read_parquet("results/parquet_cache/msmarco_train_0000.parquet")
df = df.dropna(subset=["query", "answers"])

out_dir = Path("data/eval")
out_dir.mkdir(parents=True, exist_ok=True)

added = set()
count = 0
with open(out_dir / "eval_queries.jsonl", "w", encoding="utf-8") as f:
    for row_idx, row in df.iterrows():
        q = row["query"]
        if q in added:
            continue
        
        # Get answers
        ans_arr = row["answers"]
        if hasattr(ans_arr, "tolist"):
            ans_arr = ans_arr.tolist()
        if not ans_arr or len(ans_arr) == 0:
            continue
        ans = ans_arr[0]
        if not ans or len(ans.strip()) < 5:
            continue
            
        # Get gold passage IDs
        gold_ids = []
        passages_data = row.get("passages")
        if isinstance(passages_data, dict):
            selected = passages_data.get("is_selected", [])
            query_id = row.get("query_id", row_idx)
            for p_idx, s in enumerate(selected):
                if s == 1:
                    gold_ids.append(f"msmarco-0-{query_id}-{p_idx}")
        
        if not gold_ids:
            continue
            
        added.add(q)
        f.write(json.dumps({
            "query_id": str(row.get("query_id", row_idx)),
            "query": str(q), 
            "reference_answer": str(ans),
            "gold_passage_ids": gold_ids,
            "total_relevant": len(gold_ids),
            "split": "test"
        }) + "\n")
        
        count += 1
        if count >= 100:
            break

print(f"Created eval_queries.jsonl with {count} queries, answers, and gold_passage_ids.")
