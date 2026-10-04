import requests
import json

def test_query(q, session=None):
    payload = {'query': q, 'top_k': 3, 'route': 'auto'}
    if session:
        payload['session'] = session
    res = requests.post('http://localhost:8000/search', json=payload).json()
    
    print(f"\nQUERY: '{q}'")
    if session:
        print(f"SESSION: {session}")
        
    if res.get('route_result') and res['route_result'].get('strategy') != 'off':
        rr = res['route_result']
        print(f"[ROUTER] Strategy: {rr['strategy'].upper()} | Domain: {rr['domain']} | Conf: {rr['confidence']:.2f}")
        if res.get('needs_clarification'):
            print(f"[ROUTER] Ambiguous! Suggested domains: {', '.join(res['clarification_options'])}")
            
    print(f"[RESULTS] Returned {len(res.get('results', []))} passages.")
    for idx, doc in enumerate(res.get('results', [])):
        print(f"  {idx+1}. [Tenant: {doc.get('metadata', {}).get('tenant', 'none')}] {doc.get('text', '')[:60]}...")

test_query('What documents are required for KYC when opening a bank account?')
test_query('Documents required for a home loan')
test_query('What documents are needed?')
test_query('What documents are required for KYC?', session={'tenant': 'bank_B'})
