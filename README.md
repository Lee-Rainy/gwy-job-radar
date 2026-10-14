# gd-job-radar（gwy-job-radar）

广东省公务员、事业单位招聘岗位自动采集与 QQ 邮箱早晚简报系统。  
招聘范围：广东省；关注城市：广州、东莞、佛山；信息源以各级政府公开网站为主。

## 技术栈

| 能力 | 依赖 |
|------|------|
| 容器与数据库 | Docker、PostgreSQL |
| 采集 | httpx、BeautifulSoup4、lxml、Playwright（动态页） |
| 解析 | pandas、openpyxl、PyMuPDF |
| 存储 | SQLAlchemy + psycopg |
| 邮件 | Jinja2 + SMTP（QQ 邮箱） |
| 调度 | APScheduler（容器内常驻；宿主机可用 cron 调用 CLI） |

## 项目结构

```
app/
├── main.py              # CLI：init-db / collect / send-digest / serve
├── config.py
├── database.py          # 三张表 ORM
├── scheduler.py
├── pipeline.py          # 采集 → 解析 → 入库 → 简报
├── collectors/          # 省级 + 广莞佛官方源
├── parsers/
├── services/
├── repositories/
└── templates/daily_digest.html
```

## 数据表

- **announcements**：公告元数据、`content_hash` 变更检测、`source_id + canonical_url` 唯一。
- **jobs**：岗位明细、`announcement_id + record_hash` 唯一，`raw_data` 保留原始字段 JSON。
- **email_deliveries**：按日期、早晚刊、收件人、`content_hash` 防重复发送。

字段定义见 `app/database.py` 与需求文档。

## 采集器接口

所有采集器继承 `app.collectors.base.BaseCollector`：

1. `fetch_list()` — 列表页，返回 `RawAnnouncement`（可无正文）。
2. `enrich(item)` — 详情页，补充 `html_body`、附件、发布时间。
3. `collect()` — 串行 enrich，错误写入 `CollectorResult.errors` 不中断其他条目。

合规要求：仅访问公开页面、设置 `HTTP_USER_AGENT`、遵守 `COLLECTOR_RATE_LIMIT_SECONDS`、不绕过登录或验证码。

## 数据源栏目登记

各官方栏目的列表 URL、状态（`live` / `stub`）以 **[docs/sources.yaml](docs/sources.yaml)** 为准。探活：

```powershell
$env:PYTHONPATH = "."
python -m app.main doctor --sources
```

`gz_rsj` 详情页会跟 **报名类外链** 解析报名时段与招聘条件，并写入岗位 `registration_*`（公告级时间对同公告下岗位补全）。

## 快速开始

### 1. 环境

```powershell
cd D:\gwy-job-radar
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
copy .env.example .env.test
```

**环境文件约定**（仅两个文件）：

| 文件 | 用途 |
|------|------|
| `.env.example` | 模板，占位值，可提交 git |
| `.env.test` | 你的真实配置，**已 gitignore** |

应用**自动读取**项目根目录下的 `.env.test`（也可用 `ENV_FILE` 指向其它路径）。**不会**加载 `.env` 或 `.env.example`。

### 2. PostgreSQL（本机无 Docker 时）

### PostgreSQL 命令行（psql 找不到时）

安装程序默认**不会**把 `psql` 加入 Path，在项目根目录执行：

```powershell
.\scripts\configure-postgres-env.ps1
```

重新打开终端后可用 `psql --version`。未配置 Path 时也可用：

```powershell
.\scripts\psql.ps1 -U postgres -h 127.0.0.1 -c "SELECT 1"
```

已用 winget 安装 **PostgreSQL 17** 时，安装向导里请设置 `postgres` 超级用户密码，完成后：

```powershell
$env:PGPASSWORD = "你的postgres密码"
.\scripts\setup-local-db.ps1
$env:PYTHONPATH = "."
.\.venv\Scripts\python.exe -m app.main init-db
.\.venv\Scripts\python.exe -m app.main doctor
```

有 Docker 时也可：`docker compose up -d db`。

### 一键启动（推荐）

```powershell
cd D:\gwy-job-radar
.\start.ps1
```

若提示无法运行脚本，先执行：`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`  
也可双击 `start.cmd`，或只跑一轮：`.\start-once.ps1`

**不要**在未激活虚拟环境时直接用系统 `python -m app.main`，应使用 `.\.venv\Scripts\python.exe` 或先 `.\.venv\Scripts\activate`。

### 3. 初始化与试运行

```bash
set PYTHONPATH=.
python -m app.main init-db
python -m app.main collect
python -m app.main send-digest --period morning
```

### 4. 常驻调度（Docker 全栈）

```bash
docker compose up --build
```

`app` 服务执行 `python -m app.main serve`，按 `.env.test` 中早晚时间触发：先采集再发邮件。

**上传到 GitHub + 自有服务器部署**见 [docs/DEPLOY.md](docs/DEPLOY.md)。

### QQ 邮箱

在 QQ 邮箱开启 SMTP，使用授权码填入 `SMTP_PASSWORD`。多个收件人用逗号分隔 `MAIL_RECIPIENTS`。

## 推荐开发顺序

1. **基础设施**：`config.py`、`database.py`、`init-db`、Docker Compose 联调 PostgreSQL。
2. **领域模型与仓储**：`repositories/*`，手工插入/查询验证三表约束。
3. **去重与匹配**：`deduplicate.py`、`matcher.py` + 单元测试（已完成骨架测试）。
4. **解析器**：先固定 1～2 份真实职位表（Excel/HTML），完善 `excel_parser` / `html_parser` 列映射。
5. **省级采集器**：`gd_gwy.py`、`gd_sydw.py` — 确认当期官方列表 URL 与选择器，附件下载到 `data/`。
6. **地市补充源**：`gz.py`、`dg.py`、`fs.py` — 仅作省级未覆盖时的补充，避免重复源。
7. **Playwright**：仅对必须执行 JS 的栏目增加浏览器采集，与 httpx 共用 `BaseCollector` 子类。
8. **简报与邮件**：`daily_digest.html`、`digest.py`、`mailer.py`，用 `send-digest` 本地试发。
9. **发送幂等**：`email_deliveries` 相同 `content_hash` 不重复发送。
10. **调度与监控**：`scheduler.py`、日志 `logs/app.log`，生产用 Docker healthcheck / 外部监控。

## 测试

```bash
set PYTHONPATH=.
pytest
```

## 说明

当前 `gd_gwy` / `gd_sydw` / 地市采集器为**合规占位实现**（列表选择器需按当期官网栏目填写）。解析与邮件、数据库、调度链路已打通，填入真实 URL 与表格映射后即可投产。
