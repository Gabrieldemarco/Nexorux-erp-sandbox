import json
import urllib.parse
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8002/api/v1"

creds = {
    "username": "admin@demo.com",
    "password": "demo1234",
}

req = urllib.request.Request(
    f"{BASE_URL}/auth/token",
    data=urllib.parse.urlencode(creds).encode(),
    method="POST",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
with urllib.request.urlopen(req) as r:
    token_data = json.loads(r.read().decode())
print(token_data)
access_token = token_data["access_token"]
req = urllib.request.Request(
    f"{BASE_URL}/auth/me",
    method="GET",
    headers={"Authorization": f"Bearer {access_token}"},
)
try:
    with urllib.request.urlopen(req) as r:
        print(r.status)
        print(r.read().decode())
except urllib.error.HTTPError as error:
    print("HTTP", error.code, error.reason)
    if error.fp:
        print(error.fp.read().decode())
    raise
