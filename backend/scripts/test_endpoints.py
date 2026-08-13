import json
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://127.0.0.1:8000/api/v1"


def post_form(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())


def request_json(path, token, method="GET"):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as error:
        body = error.read().decode() if error.fp else None
        print(f"HTTP {error.code} {error.reason}: {body}")
        raise


if __name__ == "__main__":
    print("Logging in...")
    token_data = post_form("/auth/token", {
        "username": "admin@demo.com",
        "password": "demo1234",
    })
    print("login ok")

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    print("Testing /auth/me")
    try:
        me_data = request_json("/auth/me", access_token)
        print(me_data)
    except urllib.error.HTTPError:
        print("/auth/me failed")
        raise

    print("Testing /tenants")
    tenants = request_json("/tenants", access_token)
    print("tenants", len(tenants))

    print("Testing /companies")
    companies = request_json("/companies", access_token)
    print("companies", len(companies))

    print("Refreshing token...")
    refresh_data = request_json("/auth/refresh", refresh_token, method="POST")
    print(refresh_data)
