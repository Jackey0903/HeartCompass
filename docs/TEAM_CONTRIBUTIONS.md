# HeartCompass 团队分工明细

**项目：** HeartCompass（Digital Immortality / 数字永生）  
**版本：** v1.0.0  
**团队规模：** 4 人  
**总工作量：** 624 小时（298 小时实际完成）

---

## 一、Tian Bu（Charlie）— 项目负责人 / CLI 框架 / 版本发布

**Git 提交：** 161 次 | **负责模块：** WP5.1, WP5.2, WP4.2/4.3（部分）

### 项目 Charter 与规划
- Project Charter 编写：项目概述、目标、成功标准、范围边界、假设与风险
- RBS（责任分解结构）→ WBS（工作分解结构）可追溯性矩阵
- Gantt 图（11 周任务级时间线）、关键路径分析
- 跨文档一致性审计（5 份文档，30+ 检查项）

### CLI 框架开发 (WP5.1)
- `immortality` 命令树架构设计（6 个子命令：doctor / setup / auth / fr / logs / lark-service）
- `--json` 输出模式：所有命令支持机器可读 JSON 格式
- man-style 帮助页面：每个子命令的完整参数文档
- 交互式 CLI：questionary + rich 终端美化、ANSI 颜色方案

### CLI Auth 系统 (WP5.2)
- auth login/logout/whoami/modify-password/bind-lark 完整认证流程
- JWT token 刷新机制（exponential backoff 重试）
- 本地 session 持久化（`~/.immortality/session.json`）
- session 过期边界条件修复

### 版本管理
- v0.5.0-dev → v1.0.0-rc1 → v1.0.0 三次 release 管理
- WBS milestone tracking 维护（Week 8 → Week 11）
- 第四、五次 Biweekly Report 编写

### 对应源码
```
src/cli/main.py              # CLI 入口，argparse 参数解析
src/cli/commands/index.py    # doctor / setup / logs 命令
src/cli/commands/auth.py     # login / register / logout / whoami / modify-password / bind-lark
src/cli/session.py           # 本地 session 持久化
src/cli/utils.py             # CLI 工具函数，格式化输出
src/cli/constants.py         # ANSI 颜色，路径常量
src/cli/assets/              # .env.example / docker-compose.yml / init-db.sh
```

---

## 二、Haojie Hu（Jackey0903）— 核心开发 / 人物画像流水线 / DevOps / 测试负责人

**Git 提交：** 56 次 | **负责模块：** WP2（部分）, WP5.2（部分）, WP5.3, WP5.4, R3.2

### 人物画像构建流水线 (WP2)
- **FRBuildingGraph 完整实现：** 11 节点顺序流水线
  ```
  LoadFR → PreprocessInput → PersistOriginalSource
    → ExtractFRIntrinsicCandidates → PlanFRIntrinsicUpdate
    → PersistFRIntrinsicUpdate → ExtractFineGrainedFeeds
    → PlanFineGrainedFeedUpsert → PersistFineGrainedFeedUpsert
    → BuildOutput → GenerateReport
  ```
- FR 核心字段比较/合并逻辑：MBTI、字符串字段、列表字段、words 字段
- FineGrainedFeed 四维度提取（PERSONALITY / INTERACTION_STYLE / PROCEDURAL_INFO / MEMORY）
- 语义召回 + 去重 + update/conflict 规划
- 异步并发锁（`asyncio.Lock`）：防止重复构建
- 冲突检测（ConflictStatus 5 种状态）

### 数据库层
- SQLAlchemy ORM：9 个模型（User, FigureAndRelation, FineGrainedFeed, OriginalSource, FineGrainedFeedConflict, FROverallUpdateLog, FRBuildingGraphReport, Knowledge, Analysis）
- 10 个枚举类型（Gender, MBTI, FigureRole, FineGrainedFeedDimension 等）
- pgvector HNSW 向量索引（1024 维，cosine distance）
- Alembic 迁移配置
- 连接池管理（pool_size=5, max_overflow=10, pool_pre_ping=True）

### Docker / DevOps (WP5.3)
- Docker Compose 配置：PostgreSQL 16 + pgvector
- 自定义 pgvector 健康检查 SQL probe（解决竞态条件）
- 30 次冷启动周期测试 → 零故障
- Docker volume 持久化修复（collation version mismatch 处理）

### 集成测试 (WP5.4)
- 8 个关键路径测试场景设计
- 全集成测试套件执行（30 个 WBS task 输出验证）
- 最终测试文档（736 行，覆盖 R1.1→R3.1 全部 RBS 需求）

### CI/CD (R3.2)
- Global AI Rules 代码审查自动化
- Conventional Commits changelog 自动生成
- Commit Quality Reviewer pre-commit 验证脚本

### 代码审计与修复
- 全仓库审计（48 个 Python 源文件，~8,980 行）
- 修复 23 个文件的 `//` 语法错误（14 个 .py + 9 个非 Python 文件）
- 补全缺失的 `FRBuildingGraph/graph.py`（11 节点 StateGraph 定义）
- 修复测试文件错误：`ConflictStatus.RESOLVED_KEEP_NEW` → `RESOLVED_ACCEPT_NEW`
- 清理 `ConversationGraph/nodes.py` 中的调试 `print()`

### 文档产出
| 文档 | 行数 | 内容 |
|------|------|------|
| CODE_REVIEW.md | 222 | 完整代码审计报告 |
| docs/ARCHITECTURE.md | 872 | 系统架构文档 |
| docs/DEPLOYMENT.md | 1,050 | 部署指南 |
| docs/DEVELOPMENT.md | 1,030 | 开发指南 |
| docs/USER_GUIDE.md | 1,120 | 用户手册 |
| docs/DATABASE.md | 1,330 | 数据库设计文档 |

### 测试扩展
| 测试文件 | 行数 | 用例数 |
|----------|------|--------|
| tests/ConversationGraph/test_full_pipeline.py | 1,560 | 45+ |
| tests/FRBuildingGraph/test_build_pipeline.py | 1,818 | 60+ |

### 实验报告
- Experiment 2-1：软件规模度量
- Experiment 2-2：软件成本估算（COCOMO II）
- Experiment 3：软件工程项目经济评估

### 对应源码
```
src/agents/graphs/FRBuildingGraph/   # 全部（graph.py / nodes.py / state.py）
src/database/                         # index.py / models.py / enums.py
src/database/alembic/                 # Alembic 迁移配置
src/services/fine_grained_feed.py     # Feed CRUD + 向量召回
src/services/figure_and_relation.py   # FR CRUD + 人物构建
alembic/versions/001_init.py          # 数据库迁移脚本
tests/                                # 全部测试文件
scripts/                              # 文档生成脚本
docs/                                 # 全部项目文档
```

---

## 三、Yihan Liu — 对话系统 / NLP 工程师 / Prompt 优化

**Git 提交：** 39 次 | **负责模块：** WP3.1 → WP3.6（全部）

### 对话系统核心 (WP3.1-3.2)
- **ConversationGraph：** 4 节点 DAG 流水线设计
  ```
  ┌─────────────────────────┐
  │  nodeLoadFRAndPersona    │ 加载 FR + 生成 persona markdown
  └──────────┬──────────────┘
             │
  ┌──────────┴──────────────┐
  │                         │
  ▼                         ▼
  nodeRecallFeedsFromDB    nodeBuildAndTrimMessage
  （向量召回）              （消息组装 + 裁剪）
  └──────────┬──────────────┘
             │
             ▼
  ┌─────────────────────────┐
  │     nodeCallLLM          │ 组装 prompt → 调用 LLM → 解析响应
  └─────────────────────────┘
  ```
- persona markdown 组装：将 FR 核心字段 + 召回 feeds 拼接为结构化 prompt
- MEMORY / PROCEDURAL_INFO 双维度语义召回（pgvector cosine_distance）
- 短期记忆管理：基于轮次（round_uuid）的消息裁剪，旧消息摘要生成
- 双阈值控制：`SHORT_TERM_MEMORY_MAX_CHARS` + `SHORT_TERM_MEMORY_TARGET_CHARS`

### LLM 集成
- 火山方舟 Ark SDK 单例封装
- ChatOpenAI 兼容接口适配（langchain-openai）
- LLM 失败重试机制

### Feed 同步 (WP3.4)
- `immortality fr sync-feeds`：将 FineGrainedFeed 四维度数据合成到 FR 核心字段
- 维度权重配置（MEMORY: 1.2, PROCEDURAL_INFO: 1.1, PERSONALITY: 0.9, INTERACTION_STYLE: 0.8）

### 话题分段摘要 (WP3.5)
- 跨话题上下文泄漏消除（context bleed elimination）
- 20/20 场景通过率 100%
- 长对话话题切换阈值调优

### Prompt 优化 (WP3.6)
- **Phase 1：** 反重复机制（-35% repetition rate）、正式度按 FigureRole 分层调优
- **Phase 2：** 情感感知语调适配、中文文化语境适配
- Token 消耗降低 22%
- 8 种 FigureRole 各独立 prompt 风格（self / family / friend / mentor / colleague / partner / public_figure / stranger）

### 测试
- 对话连贯性测试套件：30 个场景（多轮对话 + 话题切换）
- 文化适配测试：10 个场景
- 反重复和正式度回归测试

### 对应源码
```
src/agents/graphs/ConversationGraph/   # 全部（graph.py / nodes.py / state.py）
src/agents/prompts/conversation.py     # 正式度等级 + 反重复指令 + 风格注入
src/agents/prompt.py                   # Prompt Minder URL 提取
src/agents/adapter.py                  # 消息格式转换
src/agents/llm.py                      # LLM 初始化（ChatOpenAI + Ark SDK）
src/agents/embedding.py                # 多模态向量化（text/image/mixed）
src/agents/graphs/checkpointer.py      # PostgresSaver 单例
src/services/knowledge.py              # 知识库 CRUD + 向量召回
```

---

## 四、Leishiyu Chen — 飞书 Bot 集成 / 频道层 / 前端交互

**Git 提交：** 38 次 | **负责模块：** WP2（部分）, WP4.1 → WP4.6

### 飞书 WebSocket 连接 (WP4.1)
- Lark/Feishu WebSocket 事件接收与消息处理
- open_id → user_id 映射（`session.py` 集成）
- 事件驱动消息分发架构

### Bot 菜单命令 (WP4.2)

| 命令 | 功能 |
|------|------|
| `/menu` | 显示帮助菜单 |
| `/list_available_persons` | 列出所有可用对话对象 |
| `/<fr_id>` | 切换到指定人物分身 |
| `/clear_current_person` | 清除当前对话上下文 |
| `/show_persona:<fr_id>` | 查看人物画像（支持语义搜索） |
| `/build_persona:<fr_id>` | 构建/充实人物画像 |

### 消息批处理 (WP4.3)
- 15 秒时间窗口消息批处理（group incoming messages）
- 消息去重：30 秒窗口内重复消息过滤（10 秒用于斜杠命令）
- buffer overflow 修复：重连场景下的边界条件
- timer race condition 修复：批处理定时器竞态

### WebSocket 重连 (WP4.5)
- Live Lark sandbox 环境 WebSocket 重连验证
- 断线重连时消息队列保持

### 卡片模板 (WP4.6)
- Null-safe 卡片模板渲染：空 FR 字段优雅降级显示
- 4 阶段进度指示器（persona 构建进度）
- 暗色模式调色板：跨浏览器 CSS 自定义属性

### 人物画像预处理 (WP2)
- 与 Haojie 协作：FRBuildingGraph 预处理流水线
- 内容清洗与验证
- 维度标注（included_dimensions）

### 文档
- Lark bot 用户手册（setup guide + FAQ）
- README v1.0.0 功能列表更新

### 对应源码
```
src/channels/lark/                      # 全部
  ├── client.py                         # Lark API 客户端单例
  ├── websocket.py                      # WebSocket 服务器
  ├── composite_api/im/                 # send_text / send_image / send_card / send_file
  └── integration/
      ├── index.py                      # 核心消息编排 + 批处理
      ├── menu.py                       # 6 个 bot 命令
      └── utils.py                      # sendText2OpenId / sendCard2OpenId
src/agents/llm.py                       # LLM 初始化
src/agents/ark.py                       # 火山方舟 Ark 客户端单例
```

---

## 五、汇总表

### 按 WBS 模块

| WBS | 模块名称 | 负责人 | 工作量 |
|-----|----------|--------|--------|
| WP1 | User & FR Data Foundation | Leishiyu / Haojie / Tian | 84h |
| WP2 | Persona Building & Knowledge Mgmt | Leishiyu / Haojie | 120h |
| WP3 | Conversation & Dialogue System | Yihan | 132h |
| WP4 | Channel Integration & Lark Bot | Leishiyu / Tian | 126h |
| WP5 | CLI, Harness, Packaging & Deploy | Tian / Haojie | 162h |

### 按代码模块

| 模块 | 源码目录 | 负责人 |
|------|----------|--------|
| CLI 框架 | `src/cli/` | Tian |
| 数据库层 | `src/database/` | Haojie |
| 人物画像流水线 | `src/agents/graphs/FRBuildingGraph/` | Haojie / Leishiyu |
| 对话流水线 | `src/agents/graphs/ConversationGraph/` | Yihan |
| LLM 集成 | `src/agents/` (llm, ark, embedding, prompt, adapter) | Yihan / Leishiyu |
| 飞书 Bot | `src/channels/lark/` | Leishiyu |
| 业务服务 | `src/services/` | Haojie / Yihan |
| 部署运维 | Docker, CI/CD, Alembic | Haojie |
| 文档 | `docs/` | Haojie / Tian / Leishiyu |
| 测试 | `tests/` | Haojie / Yihan |
| 项目章程 | Project Charter, WBS, 双周报告 | Tian |

### 按 Git 贡献

| 成员 | GitHub 用户 | 提交数 | 主要领域 |
|------|------------|--------|----------|
| Tian Bu | charlie-bu | 161 | CLI、项目 Charter、版本发布、双周报告 |
| Haojie Hu | Jackey0903 | 56 | 人物画像管道、Docker/DevOps、CI/CD、文档、测试 |
| Yihan Liu | bahoon | 39 | 对话系统、NLP/Prompt、记忆管理、连贯性测试 |
| Leishiyu Chen | yu03140 | 38 | 飞书 Bot、WebSocket、消息批处理、卡片 UI |
