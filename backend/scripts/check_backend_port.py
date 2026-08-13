import urllib.request
import urllib.error

ports = [8000, 8001, 8002]
for port in ports:
    url = f"http://127.0.0.1:{port}/api/v1/health"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            print(port, 'OK', response.read().decode())
    except Exception as exc:
        print(port, 'ERR', type(exc).__name__, exc)
