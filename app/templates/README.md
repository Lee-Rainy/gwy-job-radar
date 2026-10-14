# 邮件 HTML 模板

主模板：`daily_digest.html`（Jinja2 变量见 `app/services/digest.py`）。

## 免费模板参考（在线预览 / 下载）

移植到 Jinja2 时建议：**表格布局 + 内联样式**，QQ/Outlook 兼容更好。

| 站点 | 说明 |
|------|------|
| [Cerberus Email Templates](https://www.cerberusemail.com/templates) | 经典响应式邮件骨架，MIT 风格开源示例 |
| [Stripo 模板库](https://stripo.email/templates/) | 大量免费模板，浏览器预览后可导出 HTML |
| [BeeFree 模板](https://beefree.io/templates) | 拖拽编辑器 + 免费模板区 |
| [Mailchimp 模板](https://templates.mailchimp.com/) | 新闻简报类布局可参考 |
| [GitHub: responsive-html-email-template](https://github.com/leemunroe/responsive-html-email-template) | 极简单栏，适合改造成简报 |

## 本地试发

```powershell
$env:ENV_FILE = ".env.test"
python -m app.main test-smtp
python -m app.main send-digest --period evening
```

可将外部模板 HTML 粘贴到 `daily_digest.html`，保留 `{% for job in new_jobs %}` 等 Jinja 块即可。
