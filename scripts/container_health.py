import os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

host = urlsplit(os.environ.get("BASE_URL", "http://localhost:8000")).netloc
request = Request("http://127.0.0.1:8000/health/live", headers={"Host": host, "X-Forwarded-Proto": "https"})
with urlopen(request, timeout=3) as response:
    assert response.status == 200
