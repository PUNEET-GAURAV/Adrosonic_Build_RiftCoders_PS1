import re

with open('src/trustrag/api/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_endpoint = '''
    @app.get("/eval-results")
    def eval_results() -> dict[str, Any]:
        import json
        from pathlib import Path
        results_dir = Path(__file__).resolve().parents[3] / "results"
        data = {}
        for mode in ["dense", "hybrid", "hybrid_rerank"]:
            try:
                p = results_dir / f"ragas_{mode}_test.json"
                if p.exists():
                    d = json.loads(p.read_text(encoding="utf-8"))
                    data[mode] = d.get("aggregate", {})
            except Exception:
                pass
        return data

    @app.exception_handler(Exception)
'''

code = code.replace('    @app.exception_handler(Exception)', new_endpoint)

with open('src/trustrag/api/app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Added /eval-results endpoint')
