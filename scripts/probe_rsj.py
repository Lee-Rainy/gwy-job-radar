import re
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

BASE = "https://rsj.gz.gov.cn"
CHANNELS = [
    "/zwdt/tzgg/index.html",
    "/zwdt/gzdt/index.html",
    "/zwdt/tpxw/index.html",
]

KEYWORDS = ("招聘", "招考", "公开", "遴选", "选调", "事业", "雇员", "劳动", "岗位")


def main() -> None:
    client = httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True)
    for ch in CHANNELS:
        url = BASE + ch
        r = client.get(url)
        print("===", url, r.status_code, len(r.text))
        soup = BeautifulSoup(r.text, "lxml")
        hits = 0
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            if "2026" not in title:
                continue
            if not any(k in title for k in KEYWORDS):
                continue
            hits += 1
            print(title[:100], a["href"][:80])
        print("hits", hits)
        for m in re.findall(r'["\']([^"\']*(?:postList|getList|channel)[^"\']*)["\']', r.text):
            if len(m) < 120:
                print("script ref:", m)
    client.close()


if __name__ == "__main__":
    main()
