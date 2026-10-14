from app.parsers.html_parser import extract_text_summary, parse_html_job_table


def test_parse_html_job_table() -> None:
    html = """
    <table>
      <tr><th>岗位名称</th><th>招聘单位</th><th>城市</th></tr>
      <tr><td>综合管理岗</td><td>某局</td><td>广州</td></tr>
    </table>
    """
    rows = parse_html_job_table(html)
    assert len(rows) == 1
    assert rows[0].job_title == "综合管理岗"
    assert rows[0].city == "广州"


def test_extract_text_summary_strips_scripts() -> None:
    html = "<html><script>bad()</script><p>公告正文</p></html>"
    assert "公告正文" in extract_text_summary(html)
    assert "bad" not in extract_text_summary(html)
