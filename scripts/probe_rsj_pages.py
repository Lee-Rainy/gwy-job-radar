import httpx
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
KW = ("招聘", "招考", "公开", "遴选", "选调", "事业", "岗位", "聘", "雇")
YEAR = "2026"

client = httpx.Client(headers=HEADERS, timeout=30)
found = []
for section in ("tzgg", "gzdt"):
    for page in range(1, 16):
        path = f"/zwdt/{section}/index.html" if page == 1 else f"/zwdt/{section}/index_{page}.html"
        url = "https://rsj.gz.gov.cn" + path
        r = client.get(url)
        if r.status_code != 200:
            break
        soup = BeautifulSoup(r.text, "lxml")
        page_hits = 0
        for a in soup.find_all("a", href=True):
            t = a.get_text(strip=True)
            if YEAR not in t:
                continue
            if not any(k in t for k in KW):
                continue
            href = a["href"]
            if not href.startswith("http"):
                href = "https://rsj.gz.gov.cn" + href
            found.append((t, href))
            page_hits += 1
        print(section, page, "hits", page_hits)
        if page_hits == 0 and page > 3:
            break

print("total", len(found))
for t, h in found:
    print(t[:80])
    print(h)

client.close()
