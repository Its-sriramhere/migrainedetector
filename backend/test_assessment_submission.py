import urllib.request, urllib.error, json, sys
sys.path.insert(0, r'C:\Users\LOQ\Desktop\MigraineDetector\backend')

# Register
import uuid
email = f"test_{uuid.uuid4().hex[:8]}@example.com"
register_data = {"email": email, "password": "TestPass123!", "name": f"Test {email}"}
req = urllib.request.Request('http://localhost:8000/api/auth/register',
    data=json.dumps(register_data).encode(),
    headers={'Content-Type': 'application/json'}, method='POST')
resp = urllib.request.urlopen(req)
user = json.loads(resp.read())
token = user['access_token']
print('Registered:', email)

# Submit assessment
answers = [{"question_id": i, "answer": "Never"} for i in range(1, 15)]
payload = {"answers": answers}
req = urllib.request.Request('http://localhost:8000/api/assessment/responses',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
    method='POST')
try:
    r = urllib.request.urlopen(req, timeout=10)
    result = json.loads(r.read())
    print('Profile built:', result)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'HTTP Error {e.code}: {body[:200]}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')