import urllib.request, urllib.error

endpoints = [
    '/api/predictions/current',
    '/api/predictions/history',
    '/api/alerts',
    '/api/sensor/latest',
    '/api/datasets',
    '/api/predict',
    '/api/health',
]

for e in endpoints:
    try:
        r = urllib.request.urlopen('http://localhost:8000' + e, timeout=2)
        print(f'{e}: {r.status}')
    except urllib.error.HTTPError as ex:
        print(f'{e}: {ex.code}')
    except Exception as ex:
        print(f'{e}: ERROR - {type(ex).__name__}: {ex}')