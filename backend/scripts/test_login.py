import urllib.parse
import urllib.request

data = urllib.parse.urlencode({
    'username': 'admin@demo.com',
    'password': 'demo1234'
}).encode()
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/token',
    data=data,
    method='POST',
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
with urllib.request.urlopen(req) as r:
    print(r.status)
    print(r.read().decode())
