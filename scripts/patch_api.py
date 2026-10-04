import sys
with open('src/trustrag/api/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

feedback_code = '''
class FeedbackRequest(BaseModel):
    request_id: str
    passage_id: str
    score: int

FEEDBACK_STORE = []

@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    FEEDBACK_STORE.append(req.model_dump())
    return {"status": "ok", "total_feedback": len(FEEDBACK_STORE)}

@app.get("/feedback-stats")
def get_feedback_stats():
    if not FEEDBACK_STORE:
        return {"upvotes": 0, "downvotes": 0, "ctr": 0.0}
    up = sum(1 for f in FEEDBACK_STORE if f['score'] == 1)
    down = sum(1 for f in FEEDBACK_STORE if f['score'] == -1)
    return {"upvotes": up, "downvotes": down, "ctr": round(up / len(FEEDBACK_STORE), 2)}
'''

if 'FEEDBACK_STORE' not in code:
    code = code.replace('@app.post("/search"', feedback_code + '\n@app.post("/search"')
    with open('src/trustrag/api/app.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print('Added feedback endpoints.')
else:
    print('Feedback already added.')
