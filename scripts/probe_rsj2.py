import httpx
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
BASE = "https://rsj.gz.gov.cn"

client = httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True)
for path in ["/", "/zwdt/tzgg/index.html", "/zwdt/gzdt/index.html"]:
    soup = BeautifulSoup(client.get(BASE + path).text, "lxml")
    print("PATH", path)
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True)
        if "招聘" in t or "招考" in t or "遴选" in t:
            print(" ", t[:60], a["href"][:80])

# site search if exists
for u in [
    "https://rsj.gz.gov.cn/search.html?keywords=2026%E6%8B%9B%E8%81%98",
    "https://rsj.gz.gov.cn/zwdt/tzgg/index_2.html",
]:
    try:
        r = client.get(u)
        print(u, r.status_code, len(r.text))
    except Exception as e:
        print(u, e)

client.close()
