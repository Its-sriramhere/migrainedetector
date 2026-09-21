import urllib.request, urllib.error

endpoints = [
    '/api/assessment/questions',
    '/api/assessment/responses',
    '/api/assessment/profile',
    '/api/assessment/baseline',
]

for e in endpoints:
    try:
        r = urllib.request.urlopen('http://localhost:8000' + e, timeout=2)
        print(f'{e}: {r.status}')
    except urllib.error.HTTPError as ex:
        print(f'{e}: {ex.code}')
    except Exception as ex:
        print(f'{e}: ERROR - {type(ex).__name__}')