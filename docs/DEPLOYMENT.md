# HeartCompass Deployment & Operations Guide

**Author:** Haojie Hu (Jackey0903)  
**Date:** 2026-06-28  
**Version:** 1.0.0

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start](#2-quick-start)
3. [Detailed Installation](#3-detailed-installation)
4. [Database Setup](#4-database-setup)
5. [Lark Bot Configuration](#5-lark-bot-configuration)
6. [Environment Configuration Reference](#6-environment-configuration-reference)
7. [Production Deployment](#7-production-deployment)
8. [Monitoring & Logging](#8-monitoring--logging)
9. [Backup & Recovery](#9-backup--recovery)
10. [Troubleshooting](#10-troubleshooting)
11. [Maintenance Procedures](#11-maintenance-procedures)
12. [Security Hardening](#12-security-hardening)
13. [Performance Tuning](#13-performance-tuning)
14. [Upgrade Guide](#14-upgrade-guide)

---

## 1. Prerequisites

### 1.1 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Operating System | macOS 12+ / Ubuntu 20.04+ / Windows 10+ | Ubuntu 22.04 LTS |
| Python | 3.11 | 3.12+ |
| RAM | 4 GB | 8 GB |
| Disk Space | 2 GB | 10 GB (for logs and database growth) |
| PostgreSQL | 14+ with pgvector | 16 with pgvector |
| Docker | 24.0+ (optional, for DB) | 26.0+ |
| Network | Outbound HTTPS (port 443) | Stable broadband |

### 1.2 Required Accounts

- **Volcengine Ark Account**: For LLM API access (doubao models + embeddings)
  - Sign up at: https://console.volcengine.com/ark
  - Create API key with model access permissions
  - Subscribe to required model endpoints

- **Lark/Feishu Developer Account**: For bot integration
  - Sign up at: https://open.feishu.cn
  - Create a bot application
  - Obtain App ID and App Secret
  - Configure bot permissions (message read/write)

### 1.3 Software Dependencies

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
python --version  # should be >= 3.11

# Install PostgreSQL with pgvector (if not using Docker)
# macOS:
brew install pgvector
# Ubuntu:
sudo apt install postgresql-16 postgresql-16-pgvector
```

---

## 2. Quick Start

### 2.1 Clone and Install

```bash
# Clone repository
git clone https://github.com/Jackey0903/HeartCompass.git
cd HeartCompass

# Install dependencies
uv sync

# Verify CLI works
uv run immortality --help
```

### 2.2 One-Command Setup

```bash
# Run interactive setup wizard
uv run immortality setup

# Follow the prompts:
# 1. Choose "Docker setup" (recommended) or "Manual setup"
# 2. For Docker: container will be auto-provisioned
# 3. For Manual: enter PostgreSQL credentials
# 4. Enter Ark API key
# 5. Enter model endpoint IDs
# 6. Enter Lark bot credentials
```

### 2.3 Verify Installation

```bash
# Run system health check
uv run immortality doctor

# Expected output (all checks pass):
# 『Immortality』[success] Doctor check passed
```

### 2.4 Start Lark Bot

```bash
# Start the Lark bot service
uv run immortality lark-service start

# The bot will connect to Lark and begin listening for messages
# Check ~/.immortality/logs/app-YYYYMMDD.log for operation logs
```

---

## 3. Detailed Installation

### 3.1 Virtual Environment Setup

```bash
# Create virtual environment
uv venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install in development mode
uv pip install -e .
```

### 3.2 Environment File Creation

The `.env` file is created at `~/.immortality/.env` by the `setup` command. It contains:

```bash
# Database Configuration
DATABASE_URI=postgresql://immortality:immortality_password@127.0.0.1:5432/immortality
CHECKPOINT_DATABASE_URI=postgresql://immortality:immortality_password@127.0.0.1:5432/immortality_checkpoint

# Authentication
ALGORITHM=HS256
LOGIN_SECRET=<randomly-generated-32-char-hex>

# Ark LLM Configuration
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_API_KEY=<your-ark-api-key>
LITE_MODEL=<your-lite-model-endpoint-id>
MINI_MODEL=<your-mini-model-endpoint-id>

# Embedding Configuration
EMBEDDING_MODEL_NAME=<embedding-model-name>
EMBEDDING_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
EMBEDDING_MODEL=<your-embedding-endpoint-id>

# Lark Bot Configuration
LARK_APP_ID=<your-lark-app-id>
LARK_APP_SECRET=<your-lark-app-secret>
LARK_CARD_TEMPLATE_ID=<your-card-template-id>

# FR Building Prompt URLs (14 prompts)
FR_BUILDING_PREPROCESS=<prompt-minder-url>
FR_BUILDING_EXTRACT_FR_INTRINSIC_CANDIDATES=<prompt-minder-url>
FR_BUILDING_COMPARE_FIELD=<prompt-minder-url>
FR_BUILDING_COLLEAGUE=<prompt-minder-url>
FR_BUILDING_FAMILY=<prompt-minder-url>
FR_BUILDING_FRIEND=<prompt-minder-url>
FR_BUILDING_MENTOR=<prompt-minder-url>
FR_BUILDING_PARTNER=<prompt-minder-url>
FR_BUILDING_PUBLIC_FIGURE=<prompt-minder-url>
FR_BUILDING_SELF=<prompt-minder-url>
FR_BUILDING_PERSONALITY=<prompt-minder-url>
FR_BUILDING_INTERACTION_STYLE=<prompt-minder-url>
FR_BUILDING_PROCEDURAL_INFO=<prompt-minder-url>
FR_BUILDING_MEMORY=<prompt-minder-url>
FR_BUILDING_REPORT=<prompt-minder-url>

# Feed Sync Configuration
SYNC_PERSONALITY_FEEDS_TO_FR_CORE=personality-dimension
SYNC_INTERACTION_FEEDS_TO_FR_CORE=interaction-dimension
SYNC_PROCEDURAL_FEEDS_TO_FR_CORE=procedural-dimension
SYNC_MEMORY_FEEDS_TO_FR_CORE=memory-dimension

# Conversation Configuration
SUMMARY_MESSAGES_FOR_TRIM=<prompt-minder-url>
CONVERSATION_SYSTEM_PROMPT=<prompt-minder-url>
SHORT_TERM_MEMORY_MAX_CHARS=8000
SHORT_TERM_MEMORY_TARGET_CHARS=6000
SHORT_TERM_MEMORY_MAX_MESSAGES=50
WAITING_SECONDS_FOR_CONVERSATION=15

# Recall Tuning
TOP_K_FEEDS_FOR_COMPARE=10
TOP_K_PERSONALITY_FEEDS_FOR_CONVERSATION=5
TOP_K_INTERACTION_FEEDS_FOR_CONVERSATION=5
TOP_K_PROCEDURAL_FEEDS_FOR_CONVERSATION=8
TOP_K_MEMORY_FEEDS_FOR_CONVERSATION=8
VECTOR_CANDIDATES=100
HALF_LIFE_DAYS=90
MAX_WORDS_TO_AND_FROM_FIGURE=10
```

### 3.3 Manual Verification

```bash
# Test database connection
uv run python -c "
from src.database.index import session
with session() as db:
    result = db.execute('SELECT 1').scalar()
    print(f'Database OK: {result}')
"

# Test LLM connectivity
uv run python -c "
from src.agents.ark import arkClient
client = arkClient()
print(f'Ark client OK: {client is not None}')
"

# Test Lark client
uv run python -c "
from src.channels.lark.client import larkClient
client = larkClient()
print(f'Lark client OK: {client is not None}')
"
```

---

## 4. Database Setup

### 4.1 Option A: Docker Setup (Recommended)

```bash
# Interactive setup will auto-provision PostgreSQL container
uv run immortality setup
# Select "Docker setup (recommended)"

# The setup will:
# 1. Check Docker and Docker Compose availability
# 2. Write docker-compose.yml to ~/.immortality/
# 3. Start PostgreSQL container with pgvector
# 4. Wait for port 5432 to become available
# 5. Create immortality_checkpoint database
# 6. Initialize all tables and extensions
```

### 4.2 Option B: Manual PostgreSQL Setup

```bash
# PostgreSQL 16 installation (Ubuntu)
sudo apt update
sudo apt install postgresql-16 postgresql-16-pgvector

# Create databases
sudo -u postgres psql <<SQL
CREATE USER immortality WITH PASSWORD 'immortality_password';
CREATE DATABASE immortality OWNER immortality;
CREATE DATABASE immortality_checkpoint OWNER immortality;

\c immortality
CREATE EXTENSION IF NOT EXISTS vector;
GRANT ALL PRIVILEGES ON DATABASE immortality TO immortality;

\c immortality_checkpoint
CREATE EXTENSION IF NOT EXISTS vector;
GRANT ALL PRIVILEGES ON DATABASE immortality_checkpoint TO immortality;
SQL

# Verify
uv run immortality doctor
```

### 4.3 Database Schema

```bash
# Tables are auto-created on first use by initDatabaseIfNeeded()
# Manual verification:
uv run python -c "
from src.database.models import initDatabaseIfNeeded
initDatabaseIfNeeded()
print('Schema initialized')
"
```

### 4.4 Migrations

```bash
# Generate migration (after model changes)
cd alembic
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1

# View migration history
alembic history
```

---

## 5. Lark Bot Configuration

### 5.1 Creating a Lark Bot Application

1. Visit https://open.feishu.cn and sign in
2. Navigate to "App Management" → "Create App"
3. Choose "Bot" type
4. Configure the bot:
   - **Name**: Immortality (or custom name)
   - **Description**: AI Digital Persona Assistant
   - **Avatar**: Upload bot icon

### 5.2 Permissions Configuration

Enable the following permissions in the bot's "Permission Management":

```
Required OAuth Scopes:
├── im:message                        # Read messages
├── im:message:send_as_bot          # Send messages as bot
├── im:resource                     # Upload resources (images/files)
└── im:message.group_msg            # Group chat messages (optional)
```

### 5.3 Event Subscription

1. Navigate to "Event Subscription"
2. Enable "im.message.receive_v1" event
3. Subscribe to message events for bot

### 5.4 Obtaining Credentials

```
From "Credentials & Basic Info" page:
├── App ID:           cli_xxxxxxxxxxxx
├── App Secret:       xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
└── Verification Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 5.5 Card Template Setup

1. Navigate to "Card Builder" in Lark Developer Console
2. Create a new card template
3. Design the card layout with variables
4. Publish the template
5. Copy the template ID

### 5.6 Bot Verification

```bash
# After starting the bot service
uv run immortality lark-service start

# Check logs for successful WebSocket connection
tail -f ~/.immortality/logs/app-$(date +%Y%m%d).log | grep "WebSocket"

# Expected log output:
# [INFO] Lark WebSocket connected successfully
# [INFO] Event handler registered for im.message.receive_v1
```

---

## 6. Environment Configuration Reference

### 6.1 Required Variables (Complete List)

| Category | Variable | Type | Description |
|----------|----------|------|-------------|
| Database | `DATABASE_URI` | URL | Main database connection string |
| Database | `CHECKPOINT_DATABASE_URI` | URL | LangGraph checkpointer database |
| Auth | `ALGORITHM` | String | JWT signing algorithm (HS256) |
| Auth | `LOGIN_SECRET` | String | JWT signing secret |
| LLM | `ARK_BASE_URL` | URL | Ark API base URL |
| LLM | `ARK_API_KEY` | String | Ark API authentication key |
| LLM | `LITE_MODEL` | String | Primary model endpoint ID |
| LLM | `MINI_MODEL` | String | Lightweight model endpoint ID |
| Embed | `EMBEDDING_MODEL_NAME` | String | Embedding model identifier |
| Embed | `EMBEDDING_BASE_URL` | URL | Embedding API base URL |
| Embed | `EMBEDDING_MODEL` | String | Embedding endpoint ID |
| Lark | `LARK_APP_ID` | String | Lark bot application ID |
| Lark | `LARK_APP_SECRET` | String | Lark bot application secret |
| Lark | `LARK_CARD_TEMPLATE_ID` | String | Card template ID |

### 6.2 Tuning Variables

| Variable | Default | Range | Description |
|----------|---------|-------|-------------|
| `SHORT_TERM_MEMORY_MAX_CHARS` | 8000 | 2000-32000 | Max characters in short-term memory |
| `SHORT_TERM_MEMORY_TARGET_CHARS` | 6000 | 1000-24000 | Target after trimming |
| `SHORT_TERM_MEMORY_MAX_MESSAGES` | 50 | 10-200 | Max message count before trim |
| `WAITING_SECONDS_FOR_CONVERSATION` | 15 | 5-60 | Message batch delay |
| `TOP_K_FEEDS_FOR_COMPARE` | 10 | 3-30 | Feeds for comparison in upsert |
| `TOP_K_PERSONALITY_FEEDS_FOR_CONVERSATION` | 5 | 1-20 | Personality feeds recalled |
| `TOP_K_INTERACTION_FEEDS_FOR_CONVERSATION` | 5 | 1-20 | Interaction feeds recalled |
| `TOP_K_PROCEDURAL_FEEDS_FOR_CONVERSATION` | 8 | 1-30 | Procedural feeds recalled |
| `TOP_K_MEMORY_FEEDS_FOR_CONVERSATION` | 8 | 1-30 | Memory feeds recalled |
| `VECTOR_CANDIDATES` | 100 | 20-500 | Vector recall candidate pool |
| `HALF_LIFE_DAYS` | 90 | 30-365 | Time decay half-life |
| `MAX_WORDS_TO_AND_FROM_FIGURE` | 10 | 3-20 | Max words for relationship labels |

### 6.3 Sync Configuration

| Variable | Description |
|----------|-------------|
| `SYNC_PERSONALITY_FEEDS_TO_FR_CORE` | Sync personality dimension feeds to FR core |
| `SYNC_INTERACTION_FEEDS_TO_FR_CORE` | Sync interaction dimension feeds to FR core |
| `SYNC_PROCEDURAL_FEEDS_TO_FR_CORE` | Sync procedural dimension feeds to FR core |
| `SYNC_MEMORY_FEEDS_TO_FR_CORE` | Sync memory dimension feeds to FR core |
| `TOP_K_PERSONALITY_FEEDS_FOR_CORE_SYNC` | Feeds to sync for personality |
| `TOP_K_INTERACTION_FEEDS_FOR_CORE_SYNC` | Feeds to sync for interaction |
| `TOP_K_PROCEDURAL_FEEDS_FOR_CORE_SYNC` | Feeds to sync for procedural |
| `TOP_K_MEMORY_FEEDS_FOR_CORE_SYNC` | Feeds to sync for memory |

---

## 7. Production Deployment

### 7.1 Systemd Service (Linux)

```ini
# /etc/systemd/system/heartcompass-lark.service
[Unit]
Description=HeartCompass Lark Bot Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=heartcompass
Group=heartcompass
WorkingDirectory=/opt/heartcompass
Environment=PATH=/opt/heartcompass/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/opt/heartcompass/.venv/bin/python -m src.main
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/heartcompass/stdout.log
StandardError=append:/var/log/heartcompass/stderr.log

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable heartcompass-lark
sudo systemctl start heartcompass-lark

# Check status
sudo systemctl status heartcompass-lark

# View logs
sudo journalctl -u heartcompass-lark -f
```

### 7.2 Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: heartcompass
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d heartcompass"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  app:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URI: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/heartcompass
      CHECKPOINT_DATABASE_URI: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/heartcompass_checkpoint
    volumes:
      - ~/.immortality:/root/.immortality
    restart: unless-stopped

volumes:
  pgdata:
    driver: local
```

### 7.3 Dockerfile

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .
RUN uv pip install -e .

CMD ["python", "-m", "src.main"]
```

### 7.4 Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 443 ssl;
    server_name heartcompass.example.com;

    ssl_certificate /etc/ssl/heartcompass.crt;
    ssl_certificate_key /etc/ssl/heartcompass.key;

    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location / {
        return 200 'HeartCompass is running';
        add_header Content-Type text/plain;
    }
}
```

---

## 8. Monitoring & Logging

### 8.1 Log Location

```
~/.immortality/logs/
├── app-20260601.log     # Daily log files
├── app-20260602.log
└── ...
```

### 8.2 Log Format

```
[YYYY-MM-DD HH:MM:SS,mmm] [LEVEL] [module] Message
```

### 8.3 Log Viewing

```bash
# View today's logs
uv run immortality logs

# View specific date
uv run immortality logs --date 20260601

# Manual tail
tail -f ~/.immortality/logs/app-$(date +%Y%m%d).log

# Filter errors
grep "ERROR\|WARNING" ~/.immortality/logs/app-*.log
```

### 8.4 Health Check Commands

```bash
# Full system check
uv run immortality doctor --json

# Quick database check
uv run python -c "
from src.database.index import session
with session() as db:
    db.execute('SELECT 1')
print('DB healthy')
"

# Check Lark WebSocket connection
grep "WebSocket" ~/.immortality/logs/app-$(date +%Y%m%d).log | tail -5
```

### 8.5 Key Metrics to Monitor

| Metric | Check | Alert Threshold |
|--------|-------|-----------------|
| LLM Latency | `nodeCallLLM` elapsed time | > 30 seconds |
| Embedding Latency | `vectorizeText` elapsed time | > 5 seconds |
| DB Connection Pool | Pool size utilization | > 80% |
| Message Queue Depth | Pending messages per user | > 20 |
| Error Rate | ERROR log frequency | > 5 per hour |
| WebSocket Status | Connection state | Disconnected > 1 min |

---

## 9. Backup & Recovery

### 9.1 Database Backup

```bash
# Full backup
pg_dump -U immortality -h 127.0.0.1 -Fc immortality > heartcompass_$(date +%Y%m%d).dump

# Checkpoint database backup
pg_dump -U immortality -h 127.0.0.1 -Fc immortality_checkpoint > checkpoint_$(date +%Y%m%d).dump

# Automated backup script
cat > ~/.immortality/backup.sh <<'SCRIPT'
#!/bin/bash
BACKUP_DIR=~/.immortality/backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U immortality -h 127.0.0.1 -Fc immortality > $BACKUP_DIR/heartcompass_$DATE.dump
pg_dump -U immortality -h 127.0.0.1 -Fc immortality_checkpoint > $BACKUP_DIR/checkpoint_$DATE.dump
find $BACKUP_DIR -type f -mtime +30 -delete
echo "Backup completed: $DATE"
SCRIPT

# Cron: daily backup at 2am
# 0 2 * * * /bin/bash ~/.immortality/backup.sh >> ~/.immortality/backup.log 2>&1
```

### 9.2 Database Restore

```bash
# Full restore
pg_restore -U immortality -h 127.0.0.1 -d immortality --clean heartcompass_YYYYMMDD.dump

# Checkpoint restore
pg_restore -U immortality -h 127.0.0.1 -d immortality_checkpoint --clean checkpoint_YYYYMMDD.dump

# After restore, re-initialize database extensions
uv run python -c "from src.database.models import initDatabaseIfNeeded; initDatabaseIfNeeded()"
```

### 9.3 Configuration Backup

```bash
# Backup .env file
cp ~/.immortality/.env ~/.immortality/backups/.env.$(date +%Y%m%d)

# Backup session files
cp ~/.immortality/session.json ~/.immortality/backups/session.json.$(date +%Y%m%d)
```

---

## 10. Troubleshooting

### 10.1 Common Issues

#### Issue: "Doctor check failed — Database connection failed"

```bash
# Check PostgreSQL status
docker ps | grep postgres     # Docker mode
pg_isready -h 127.0.0.1       # Manual mode

# Check credentials in .env
grep DATABASE_URI ~/.immortality/.env

# Test manual connection
psql -U immortality -h 127.0.0.1 -d immortality -c "SELECT 1"
```

#### Issue: "Ark API key is invalid"

```bash
# Verify API key is set
grep ARK_API_KEY ~/.immortality/.env

# Test API key
curl -H "Authorization: Bearer $(grep ARK_API_KEY ~/.immortality/.env | cut -d= -f2)" \
  https://ark.cn-beijing.volces.com/api/v3/models
```

#### Issue: "Lark WebSocket connection failed"

```bash
# Verify app credentials
grep LARK_APP ~/.immortality/.env

# Check network connectivity
curl -I https://open.feishu.cn

# Review detailed error logs
grep -i "lark\|websocket\|error" ~/.immortality/logs/app-$(date +%Y%m%d).log | tail -20
```

#### Issue: "FRBuildingGraph is running"

```bash
# This is a concurrency guard — wait for the current build to finish
# Check build progress in logs
grep "FRBuildingGraph\|nodeLoadFR\|nodePreprocessInput" ~/.immortality/logs/app-$(date +%Y%m%d).log | tail -10

# If stuck, restart the Lark service
# (Build will be lost, need to re-submit)
```

#### Issue: "ImportError: No module named 'langgraph'"

```bash
# Re-install dependencies
uv sync --reinstall

# Verify installation
uv run python -c "import langgraph; print(langgraph.__version__)"
```

#### Issue: "psycopg.errors.UndefinedFile: could not access file 'vector'"

```bash
# pgvector extension not installed
sudo -u postgres psql -d immortality -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Or re-init database
uv run python -c "from src.database.models import initDatabaseIfNeeded; initDatabaseIfNeeded()"
```

### 10.2 Diagnostic Commands

```bash
# Full environment dump (redact secrets)
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
for key in sorted(os.environ):
    if key.startswith(('ARK_', 'LARK_', 'DB_', 'DATABASE', 'EMBEDDING')):
        val = os.environ[key]
        if 'SECRET' in key or 'KEY' in key or 'PASSWORD' in key:
            val = val[:4] + '...' + val[-4:] if len(val) > 8 else '***'
        print(f'{key}={val}')
"

# Database table counts
uv run python -c "
from src.database.index import session
from src.database.models import User, FigureAndRelation, FineGrainedFeed
with session() as db:
    print(f'Users: {db.query(User).count()}')
    print(f'FRs: {db.query(FigureAndRelation).count()}')
    print(f'Feeds: {db.query(FineGrainedFeed).count()}')
"

# Check vector index status
uv run python -c "
from src.database.index import session
with session() as db:
    result = db.execute(\"\"\"
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename IN ('fine_grained_feeds', 'knowledge')
    \"\"\").fetchall()
    for row in result:
        print(row)
"
```

---

## 11. Maintenance Procedures

### 11.1 Routine Maintenance Checklist

**Daily:**
- [ ] Check bot is responding (send test message `/menu`)
- [ ] Review logs for errors: `grep ERROR ~/.immortality/logs/app-$(date +%Y%m%d).log`
- [ ] Verify database is accessible: `uv run immortality doctor`

**Weekly:**
- [ ] Review disk usage: `du -sh ~/.immortality/`
- [ ] Rotate logs: delete logs older than 30 days
- [ ] Check LLM API quota remaining
- [ ] Verify backup integrity

**Monthly:**
- [ ] Update dependencies: `uv sync --upgrade`
- [ ] Review and optimize vector indexes
- [ ] Analyze slow queries in PostgreSQL logs
- [ ] Update Lark bot permissions if needed

### 11.2 Log Rotation

```bash
# Manual log cleanup (keep last 30 days)
find ~/.immortality/logs -name "app-*.log" -type f -mtime +30 -delete

# Cron entry for automatic rotation
# 0 3 * * * find ~/.immortality/logs -name "app-*.log" -type f -mtime +30 -delete
```

### 11.3 Database Maintenance

```sql
-- Analyze tables for query planner
ANALYZE users;
ANALYZE figure_and_relations;
ANALYZE fine_grained_feeds;
ANALYZE original_sources;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('fine_grained_feeds', 'knowledge')
ORDER BY idx_scan DESC;

-- Reindex if needed
REINDEX INDEX idx_fgf_embedding;
REINDEX INDEX idx_knowledge_embedding;
```

---

## 12. Security Hardening

### 12.1 File Permissions

```bash
# Secure the .env file
chmod 600 ~/.immortality/.env

# Secure session file
chmod 600 ~/.immortality/session.json

# Secure logs (may contain user data)
chmod 700 ~/.immortality/logs/
```

### 12.2 Database Security

```sql
-- Use strong passwords
ALTER USER immortality WITH PASSWORD 'strong_random_password_here';

-- Restrict remote access
-- In postgresql.conf:
-- listen_addresses = 'localhost'

-- In pg_hba.conf:
-- host all immortality 127.0.0.1/32 md5
```

### 12.3 API Key Management

- Rotate Ark API keys quarterly
- Rotate Lark App Secret bi-annually
- Use environment variables exclusively (never hardcode secrets)
- Add `.env` and `session.json` to `.gitignore` (already configured)

### 12.4 Network Security

```bash
# Use firewall to restrict PostgreSQL access
sudo ufw allow from 127.0.0.1 to any port 5432
sudo ufw deny 5432

# Use HTTPS for all external API calls
# (Ark SDK and Lark SDK use HTTPS by default)

# Monitor for unauthorized access attempts
grep "authentication failed\|invalid token" ~/.immortality/logs/app-*.log
```

---

## 13. Performance Tuning

### 13.1 PostgreSQL Configuration

```ini
# postgresql.conf recommended settings
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 16MB
random_page_cost = 1.1
effective_io_concurrency = 200

# For vector search performance
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
```

### 13.2 Connection Pool Tuning

```python
# In src/database/index.py, adjust these for your workload:
engine = create_engine(
    database_url,
    pool_size=5,           # Base connections (for low-traffic)
    max_overflow=10,       # Peak additional connections
    pool_pre_ping=True,    # Validate connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

### 13.3 LLM Performance

- **Model Selection**: Use MINI_MODEL for summarization to reduce latency and cost
- **Batch Processing**: Maximize context within `SHORT_TERM_MEMORY_MAX_CHARS` to reduce API calls
- **Caching**: LangGraph checkpointer caches conversation state between turns

### 13.4 Embedding Performance

- Embeddings are computed on write, not on read
- Vector search uses HNSW index for O(log N) approximate search
- `VECTOR_CANDIDATES` limits the candidate pool for re-ranking

---

## 14. Upgrade Guide

### 14.1 Version Upgrade Steps

```bash
# 1. Backup database
~/.immortality/backup.sh

# 2. Pull latest code
git pull origin main

# 3. Update dependencies
uv sync

# 4. Run database migrations (if any)
cd alembic && alembic upgrade head && cd ..

# 5. Verify with doctor check
uv run immortality doctor

# 6. Restart service
sudo systemctl restart heartcompass-lark
# or
uv run immortality lark-service start
```

### 14.2 Rollback Procedure

```bash
# 1. Stop service
sudo systemctl stop heartcompass-lark

# 2. Restore database
pg_restore -U immortality -h 127.0.0.1 -d immortality --clean latest_backup.dump

# 3. Rollback code
git checkout <previous-version-tag>

# 4. Reinstall dependencies
uv sync

# 5. Restart
sudo systemctl start heartcompass-lark
```

### 14.3 Version Compatibility Matrix

| HeartCompass | Python | PostgreSQL | pgvector | LangGraph |
|-------------|--------|------------|----------|-----------|
| 1.0.0 | >= 3.11 | 16 | 0.3.6+ | 1.0.10+ |
| 0.5.0 | >= 3.11 | 15+ | 0.3.0+ | 0.2.0+ |

---

## Appendix A: Quick Reference Cards

### A.1 Essential Commands

```bash
# Setup
uv run immortality setup              # Interactive setup
uv run immortality doctor             # Health check
uv run immortality lark-service start # Start bot

# Auth
uv run immortality auth register      # Create account
uv run immortality auth login         # Log in
uv run immortality auth bind-lark     # Bind Lark account

# FR Management
uv run immortality fr add             # Create persona
uv run immortality fr list            # List personas
uv run immortality fr show            # View persona details

# Monitoring
uv run immortality logs               # View today's logs
uv run immortality logs --date 20260601  # View specific date
```

### A.2 Directory Map

```
~/.immortality/
├── .env                    # Environment configuration
├── session.json            # Login session token
├── docker-compose.yml      # Docker Compose for PostgreSQL
├── init-db.sh              # Database initialization script
├── logs/                   # Application logs
│   ├── app-20260601.log
│   └── ...
└── backups/                # Database backups
    ├── heartcompass_*.dump
    └── checkpoint_*.dump
```

### A.3 Port Reference

| Service | Port | Protocol | External |
|---------|------|----------|----------|
| PostgreSQL | 5432 | TCP | No (localhost only) |
| Lark WebSocket | 443 | WSS | Yes (outbound) |
| Ark API | 443 | HTTPS | Yes (outbound) |

---

*Deployment guide maintained by Haojie Hu (Jackey0903). Last updated 2026-06-28.*
