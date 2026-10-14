# 上传到 GitHub 与服务器部署

## 一、上传到 GitHub（本机 Windows）

### 1. 确认不会提交密钥

以下文件已在 `.gitignore` 中，**不要**提交到 GitHub：

- `.env.test`（SMTP、数据库密码等）
- `data/` 附件与 SQLite
- `logs/`、`*.log`

仓库里只保留 [`.env.example`](../.env.example) 作为模板。

### 2. 初始化并首次提交（若尚未 git）

在项目根目录：

```powershell
cd D:\gwy-job-radar
git init -b main
git add -A
git status
# 确认列表中没有 .env.test
git commit -m "chore: initial commit for gd-job-radar"
```

### 3. 在 GitHub 创建空仓库

1. 打开 https://github.com/new  
2. 仓库名例如 `gwy-job-radar`（Private 推荐）  
3. **不要**勾选 “Add a README”（本地已有代码）  
4. 创建后复制 HTTPS 地址，例如 `https://github.com/你的用户名/gwy-job-radar.git`

### 4. 推送

```powershell
git remote add origin https://github.com/你的用户名/gwy-job-radar.git
git push -u origin main
```

若提示登录，使用 GitHub **Personal Access Token** 作为密码，或配置 SSH 密钥。

---

## 二、Linux 服务器部署（推荐 Docker）

### 环境要求

- Docker Engine + Docker Compose v2
- 能访问外网（采集 rsj.gz.gov.cn、QQ SMTP）
- 建议 2GB+ 内存（镜像含 Playwright Chromium）

### 1. 克隆代码

```bash
sudo mkdir -p /opt/gwy-job-radar
sudo chown $USER:$USER /opt/gwy-job-radar
cd /opt/gwy-job-radar
git clone https://github.com/你的用户名/gwy-job-radar.git .
```

### 2. 配置环境变量

```bash
cp .env.example .env.test
nano .env.test
```

**服务器上建议修改：**

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 使用 Compose 内网时可省略，由 `docker-compose.yml` 覆盖为 `@db:5432` |
| `SMTP_*` / `MAIL_RECIPIENTS` | QQ 邮箱授权码与收件人 |
| `COLLECTOR_SOURCES` | 例如 `gz_rsj` |
| `RUN_JOB_ON_START` | 首次可 `true` 测一轮，稳定后 `false` |
| `MORNING_DIGEST_HOUR` / `EVENING_DIGEST_HOUR` | 早晚报时间（Asia/Shanghai） |

### 3. 启动（生产：不暴露数据库端口）

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

查看日志：

```bash
docker compose logs -f app
```

### 4. 初始化数据库（首次）

```bash
docker compose exec app python -m app.main init-db
docker compose exec app python -m app.main doctor
docker compose exec app python -m app.main doctor --sources
```

可选试跑一轮：

```bash
docker compose exec app python -m app.main run-now --period evening --sources gz_rsj
```

### 5. 更新版本

```bash
cd /opt/gwy-job-radar
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 6. 防火墙与安全

- 无需对外开放 `5432`（使用 `docker-compose.prod.yml`）
- 应用无 HTTP 端口，仅定时任务出站访问官网与 SMTP
- 定期 `git pull` 前在本地跑 `pytest`

---

## 三、不用 Docker（仅 Python，可选）

适合已有 PostgreSQL 的机器：

```bash
git clone ...
cd gwy-job-radar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env.test
# 编辑 .env.test，DATABASE_URL 指向本机 Postgres
export PYTHONPATH=.
python -m app.main init-db
nohup python -m app.main serve >> logs/app.log 2>&1 &
```

更稳妥可用 **systemd** 托管 `serve` 进程（需自行编写 unit 文件）。

---

## 四、常见问题

| 现象 | 处理 |
|------|------|
| SMTP `WRONG_VERSION_NUMBER` | `.env.test` 使用 `SMTP_PORT=587`、`SMTP_USE_SSL=false` |
| 采集 403 | 已内置浏览器 UA；检查服务器 IP 是否被目标站限制 |
| 邮件重复 | 正常：`content_hash` 相同会跳过；改内容后会再发 |
| `doctor --sources` 失败 | 检查服务器出网与 DNS |
