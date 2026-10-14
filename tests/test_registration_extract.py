from app.parsers.registration_extract import (
    parse_registration_window,
    pick_registration_url,
)


def test_parse_registration_range() -> None:
    text = "网上报名时间为2026年3月1日至2026年3月10日，请按时报考。"
    start, end = parse_registration_window(text)
    assert start is not None and start.year == 2026 and start.month == 3 and start.day == 1
    assert end is not None and end.day == 10


def test_pick_registration_url_prefers_signup_link() -> None:
    html = """
    <html><body>
      <a href="/attachment/foo.xlsx">岗位表</a>
      <a href="https://www.example.com/signup">网上报名入口</a>
      <a href="/other">成绩查询</a>
    </body></html>
    """
    url = pick_registration_url(html, "https://rsj.gz.gov.cn/content/post_1.html")
    assert url == "https://www.example.com/signup"
