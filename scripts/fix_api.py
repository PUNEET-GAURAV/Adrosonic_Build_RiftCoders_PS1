import sys
with open('src/trustrag/api/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# I need to revert my patch first, then apply it properly.
if 'class FeedbackRequest' in code:
    print('Removing old patch')
    start = code.find('class FeedbackRequest')
    end = code.find('@app.post("/search"')
    code = code[:start] + '    ' + code[end:]

feedback_code = '''
    class FeedbackRequest(BaseModel):
        request_id: str
        passage_id: str
        score: int

    @app.post("/feedback")
    def submit_feedback(req: FeedbackRequest):
        app.state.feedback_store.append(req.model_dump())
        return {"status": "ok", "total": len(app.state.feedback_store)}

    @app.get("/feedback-stats")
    def get_feedback_stats():
        store = app.state.feedback_store
        if not store:
            return {"upvotes": 0, "downvotes": 0, "ctr": 0.0}
        up = sum(1 for f in store if f['score'] == 1)
        down = sum(1 for f in store if f['score'] == -1)
        return {"upvotes": up, "downvotes": down, "ctr": round(up / len(store), 2)}
'''

if 'def get_feedback_stats' not in code:
    code = code.replace('    @app.post("/search"', feedback_code + '\n    @app.post("/search"')
    code = code.replace('app.state.degraded = 0', 'app.state.degraded = 0\n    app.state.feedback_store = []')
    
    if 'BaseModel' not in code:
        code = 'from pydantic import BaseModel\n' + code

with open('src/trustrag/api/app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Fixed indentation in app.py')
