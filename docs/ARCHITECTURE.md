# HeartCompass System Architecture

**Author:** Haojie Hu (Jackey0903)  
**Date:** 2026-06-28  
**Version:** 1.0.0

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architectural Layers](#2-architectural-layers)
3. [Component Architecture](#3-component-architecture)
4. [Data Flow](#4-data-flow)
5. [LangGraph Pipeline Design](#5-langgraph-pipeline-design)
6. [Database Design](#6-database-design)
7. [LLM Integration](#7-llm-integration)
8. [Lark Bot Integration](#8-lark-bot-integration)
9. [CLI Architecture](#9-cli-architecture)
10. [Security Architecture](#10-security-architecture)
11. [Performance Considerations](#11-performance-considerations)
12. [Error Handling Strategy](#12-error-handling-strategy)
13. [Testing Architecture](#13-testing-architecture)
14. [Build and Deployment](#14-build-and-deployment)

---

## 1. System Overview

HeartCompass (Digital Immortality) is an AI-powered digital persona system that creates and maintains virtual representations of real individuals. The system ingests information about a person through multiple channels, builds a multi-dimensional persona model, and enables natural conversation with the digital persona.

### Core Capabilities

- **Multi-dimensional Persona Modeling**: Captures personality traits, interaction styles, procedural knowledge, and episodic memories across 5 fine-grained dimensions
- **Intelligent Persona Building**: LLM-powered extraction and synthesis of persona information from unstructured text inputs
- **Natural Conversation**: Context-aware dialogue generation with role-specific formality, emotional tone adaptation, and cultural context awareness
- **Multi-channel Access**: CLI interface for power users and Lark/Feishu bot for everyday interaction
- **Vector-based Memory**: Semantic recall of relevant persona information using 1024-dimensional embeddings with HNSW indexing
- **Conflict Resolution**: Built-in mechanisms for detecting and resolving contradictory information about a figure

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language Models | Volcengine Ark (Doubao 2.0 Lite/Mini) | Conversation generation, persona extraction, field comparison |
| Embeddings | Ark Multimodal Embeddings (1024-dim) | Semantic vectorization of text and images |
| Workflow Engine | LangGraph 1.0+ | State graph execution with async checkpointing |
| Database | PostgreSQL 16 + pgvector | Relational storage with HNSW vector indexing |
| ORM | SQLAlchemy 2.0 | Database abstraction with async support |
| Bot Platform | Lark/Feishu Open API (lark-oapi 1.5+) | WebSocket-based message handling |
| CLI Framework | argparse + questionary + rich | Interactive CLI with colored output and markdown rendering |
| Package Management | uv | Fast Python package management and virtual environments |
| Containerization | Docker Compose | PostgreSQL deployment with pgvector extension |

---

## 2. Architectural Layers

The system follows a clean layered architecture with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌──────────────┐  ┌──────────────────────────────────────┐ │
│  │   CLI (argparse)  │  │   Lark Bot (WebSocket + Events)    │ │
│  │   src/cli/       │  │   src/channels/lark/               │ │
│  └──────┬───────────┘  └──────────────┬───────────────────┘ │
└─────────┼──────────────────────────────┼─────────────────────┘
          │                              │
┌─────────┼──────────────────────────────┼─────────────────────┐
│         │     Integration Layer         │                     │
│  ┌──────┴──────────────────────────────┴──────────────────┐ │
│  │   Message Orchestration (integration/index.py)         │ │
│  │   - Async event loop management                        │ │
│  │   - Message batching with threading.Timer              │ │
│  │   - Duplicate detection                                │ │
│  │   - FR context switching                               │ │
│  └──────────────────────┬─────────────────────────────────┘ │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                         │    Agent Layer                     │
│  ┌──────────────────────┴─────────────────────────────────┐ │
│  │              LangGraph Pipelines                        │ │
│  │  ┌─────────────────────┐  ┌──────────────────────────┐ │ │
│  │  │ ConversationGraph   │  │   FRBuildingGraph        │ │ │
│  │  │ 4-node DAG          │  │   11-node Pipeline       │ │ │
│  │  │ (src/agents/graphs/ │  │   (src/agents/graphs/    │ │ │
│  │  │  ConversationGraph) │  │    FRBuildingGraph)      │ │ │
│  │  └─────────┬───────────┘  └────────────┬─────────────┘ │ │
│  └────────────┼──────────────────────────┼────────────────┘ │
│               │                          │                   │
│  ┌────────────┼──────────────────────────┼────────────────┐ │
│  │            │    LLM Interface          │                │ │
│  │  ┌─────────┴────────┐  ┌──────────────┴──────────────┐ │ │
│  │  │  Ark SDK (Volcengine)  │  ChatOpenAI (langchain)     │ │ │
│  │  │  - ark.py             │  - llm.py                   │ │ │
│  │  │  - embedding.py       │  - adapter.py               │ │ │
│  │  │  - prompt.py          │  - types.py                 │ │ │
│  │  └──────────────────────┘  └───────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                         │    Service Layer                   │
│  ┌──────────────────────┴─────────────────────────────────┐ │
│  │  src/services/                                          │ │
│  │  - user.py:              JWT auth, user CRUD            │ │
│  │  - figure_and_relation.py: FR CRUD, persona building    │ │
│  │  - fine_grained_feed.py: Feed CRUD, vector recall       │ │
│  │  - knowledge.py:         Knowledge base + vector search │ │
│  └──────────────────────┬─────────────────────────────────┘ │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                         │    Data Layer                      │
│  ┌──────────────────────┴─────────────────────────────────┐ │
│  │  src/database/                                          │ │
│  │  - models.py:   9 ORM models (SQLAlchemy)               │ │
│  │  - enums.py:    10 enum types                           │ │
│  │  - index.py:    Connection pool + engine factory        │ │
│  └──────────────────────┬─────────────────────────────────┘ │
└─────────────────────────┼───────────────────────────────────┘
                          │
                   ┌──────┴──────┐
                   │ PostgreSQL  │
                   │ + pgvector  │
                   └─────────────┘
```

### Layer Responsibilities

**Presentation Layer**: Handles all user interaction. The CLI provides a command-line interface for system administration (setup, auth, doctor checks). The Lark bot provides the primary user interface for persona building and conversation.

**Integration Layer**: Orchestrates message flow between the presentation and agent layers. Manages asynchronous event loops, implements message batching to reduce API calls, handles duplicate detection, and maintains per-user FR context state.

**Agent Layer**: Contains the AI pipelines. The ConversationGraph manages the dialogue flow, and the FRBuildingGraph handles persona construction from raw input. This layer also contains the LLM interface abstraction that supports both the Ark SDK for native API calls and the langchain-openai adapter for standard ChatOpenAI compatibility.

**Service Layer**: Implements all business logic. Each service module encapsulates a domain: user management, figure-and-relation operations, fine-grained feed management, and knowledge base operations. Services handle validation, ownership checks, and coordinate with the data layer.

**Data Layer**: Provides database abstraction through SQLAlchemy ORM models and a connection engine factory. Supports pgvector for vector similarity search with HNSW indexing.

---

## 3. Component Architecture

### 3.1 CLI Component (`src/cli/`)

```
src/cli/
├── main.py              # Entry point, argument parser builder
├── constants.py         # ANSI colors, ASCII art, paths (~/.immortality/)
├── session.py           # Local session persistence (JWT in JSON file)
├── utils.py             # CLIError, colored help formatter, table/markdown rendering
├── commands/
│   ├── index.py         # doctor, setup, logs subcommands
│   ├── auth.py          # login, register, logout, whoami, modify-password, bind-lark
│   ├── fr.py            # add, list, show, sync-feeds
│   └── lark_service.py  # start
└── assets/
    ├── .env.example     # Template with all 44 required environment variables
    ├── docker-compose.yml
    └── init-db.sh
```

**Design Patterns:**

- **Parser Builder Pattern**: `registerTopSubparser()`, `registerAuthSubparser()`, `registerFRSubparser()`, `registerLarkServiceSubparser()` each register their commands on the main parser. This allows modular command registration.
- **Custom Help Formatter**: `ImmortalityArgumentParser` extends `argparse.ArgumentParser` with ANSI-colored output and markdown-style formatting via `rich`.
- **Session Management**: JWT tokens are persisted to `~/.immortality/session.json`. The `getUserIdFromLocalSession()` function validates tokens and raises `CLIError` on expiry.
- **Output Adapters**: `printServiceResInCLI()` handles JSON vs human-readable output; `printTableInCLI()` renders dicts/lists as GitHub-flavored markdown tables; `printMarkdownInCLI()` renders markdown via `rich.Markdown`.

**Error Handling:**
- `CLIError(message, exit_code)`: Custom exception for expected CLI errors
- `KeyboardInterrupt`: Caught at top level, returns exit code 130
- Generic exceptions: Caught as unexpected errors, returns exit code 1

### 3.2 Lark Bot Component (`src/channels/lark/`)

```
src/channels/lark/
├── client.py                    # Lark API client singleton (@lru_cache)
├── websocket.py                 # WebSocket server, event dispatching, message adapter
├── composite_api/
│   └── im/
│       ├── send_text.py         # Send text messages via CreateMessageRequest
│       ├── send_image.py        # Upload + send image (two-phase API)
│       ├── send_card.py         # Send interactive cards with template variables
│       └── send_file.py         # Upload + send file (two-phase API)
└── integration/
    ├── index.py                 # Core orchestration: batching, dedup, async loop
    ├── menu.py                  # 6 bot commands: /menu, /list, /switch, /clear, /show_persona, /build_persona
    └── utils.py                 # sendText2OpenId, sendCard2OpenId
```

**Design Patterns:**

- **Client Singleton**: `larkClient()` uses `@lru_cache` for thread-safe lazy initialization
- **Event-Driven Architecture**: WebSocket receives P2ImMessageReceiveV1 events, `messageAdapter` extracts text content, dispatches to `messageHandler`
- **Message Batching**: Messages are buffered per-user with a configurable timer (`WAITING_SECONDS_FOR_CONVERSATION`). Each new message resets the timer. When the timer fires, all buffered messages are sent as a batch to the ConversationGraph.
- **Deduplication**: `filterDuplicatedMessage()` maintains a sliding window of recent messages. Exact duplicates within 10s (commands) or 30s (regular messages) are dropped.
- **Async Event Loop**: A dedicated daemon thread runs a persistent asyncio event loop. All async operations are scheduled via `asyncio.run_coroutine_threadsafe()`, ensuring connection reuse and stability.
- **FR Context**: Per-user state tracks the currently active FR (`_active_fr_by_open_id`), pending messages (`_pending_messages_by_open_id`), and flush timers (`_flush_timer_by_open_id`).

**Bot Commands:**

| Command | Handler | Description |
|---------|---------|-------------|
| `/menu` | `showMenuLark` | Display command list (turquoise card) |
| `/list_available_persons` | `listAvailableFRsLark` | List all available FRs |
| `/<fr_id>` | `switchFRLark` | Switch active conversation target |
| `/clear_current_person` | `clearCurrentRelationChainLark` | Clear current conversation chain |
| `/show_persona:<id>\n<query>` | `showFRLark` | Query persona with sensitive data filtering |
| `/build_persona:<id>\n<text>` | `buildPersonaLark` | Trigger FR building pipeline |

### 3.3 Agent Component (`src/agents/`)

```
src/agents/
├── llm.py                    # LLM initialization (ChatOpenAI + Ark SDK)
├── ark.py                    # Volcengine Ark client singleton
├── embedding.py              # Multimodal vectorization (text/image/mixed)
├── adapter.py                # Message format conversion
├── prompt.py                 # Prompt Minder URL extraction
├── types.py                  # Pydantic models for LLM chunk responses
├── tools.py                  # Tool definitions (reserved for future)
├── viking.py                 # VikingDB prototype (reserved for future)
├── mcp.py                    # MCP server placeholder
├── prompts/
│   └── conversation.py       # Formality levels and anti-repetition directives
└── graphs/
    ├── checkpointer.py       # PostgresSaver singleton for graph state persistence
    ├── ConversationGraph/
    │   ├── graph.py          # 4-node DAG definition + singleton pattern
    │   ├── nodes.py          # Node implementations
    │   └── state.py          # State schema, input/output TypedDicts
    └── FRBuildingGraph/
        ├── graph.py          # 11-node pipeline + async context manager
        ├── nodes.py          # Node implementations
        └── state.py          # State schema with 20+ fields
```

---

## 4. Data Flow

### 4.1 Conversation Flow

```
User sends message via Lark
        │
        ▼
Lark WebSocket receives P2ImMessageReceiveV1 event
        │
        ▼
messageAdapter extracts text content
        │
        ▼
messageHandler (integration/index.py)
    ├── filterDuplicatedMessage() — check recent duplicates
    ├── handleMenuCommand() — check if bot command
    ├── getUserIdByOpenId() — resolve user identity
    ├── Validate FR context (_active_fr_by_open_id)
    └── Enqueue message + _scheduleFlush()
            │
            ▼ (after WAITING_SECONDS_FOR_CONVERSATION)
_sendBatchMessages()
    ├── Validate user + FR ownership
    └── _runAsync(processMessages())
            │
            ▼
processMessages()
    ├── getConversationGraph() — get compiled graph
    ├── graph.ainvoke(state, config)
    │       │
    │       ▼ (LangGraph executes nodes in order)
    │   ┌─────────────────────────────────────────┐
    │   │ 1. nodeLoadFRAndPersona                 │
    │   │    - Load user from DB                  │
    │   │    - Load FigureAndRelation             │
    │   │    - Build persona markdown             │
    │   │    - Generate round_uuid for messages   │
    │   │                                         │
    │   │ 2. nodeRecallFeedsFromDB (parallel) ─┐  │
    │   │    - Vector search for PROCEDURAL_INFO│  │
    │   │    - Vector search for MEMORY         │  │
    │   │    - Apply confidence weights         │  │
    │   │    - Apply time decay                 │  │
    │   │                                       │  │
    │   │ 3. nodeBuildAndTrimMessage (parallel)─┘  │
    │   │    - Append new HumanMessage            │
    │   │    - Group messages by round_uuid        │
    │   │    - Trim to target char count           │
    │   │    - Generate rolling summary via LLM    │
    │   │                                         │
    │   │ 4. nodeCallLLM                          │
    │   │    - Assemble system prompt:            │
    │   │      CONVERSATION_SYSTEM_PROMPT         │
    │   │      + persona markdown                 │
    │   │      + recalled feeds                  │
    │   │      + conversation_summary            │
    │   │      + trimmed messages                │
    │   │    - Call Ark LLM with JSON output      │
    │   │    - Parse messages_to_send             │
    │   │    - Retry on parse failure (max 2)     │
    │   └─────────────────────────────────────────┘
    │
    └── Return (messages_to_send, reasoning_content)
            │
            ▼
sendText2OpenId() for each message
```

### 4.2 Persona Building Flow

```
User sends /build_persona:<fr_id> <text>
        │
        ▼
handleMenuCommand() dispatches to buildPersonaLark()
        │
        ▼
buildPersonaLark()
    ├── Validate user + FR ownership
    └── _runAsync(buildPersonaInBackground())
            │
            ▼
getFRBuildingGraph() — acquire async context manager (concurrency guard)
        │
        ▼
graph.ainvoke(init_state)
        │
        ▼ (LangGraph executes 11 nodes sequentially)
    ┌──────────────────────────────────────────────┐
    │ 1.  nodeLoadFR                              │
    │     - Load user profile                     │
    │     - Load FigureAndRelation                │
    │     - Determine figure_role                 │
    │     - Resolve role_recipe_path             │
    │                                              │
    │ 2.  nodePreprocessInput                     │
    │     - LLM cleans/classifies raw text        │
    │     - Detects OriginalSourceType            │
    │     - Assesses FineGrainedFeedConfidence    │
    │     - Assigns included_dimensions           │
    │                                              │
    │ 3.  nodePersistOriginalSource               │
    │     - Insert OriginalSource record          │
    │     - Return original_source_id             │
    │                                              │
    │ 4.  nodeExtractFRIntrinsicCandidates        │
    │     - LLM extracts FR intrinsic fields      │
    │       (MBTI, birthday, occupation, etc.)    │
    │     - Validates extracted values            │
    │                                              │
    │ 5.  nodePlanFRIntrinsicUpdate               │
    │     - Compare old vs new field values       │
    │     - LLM resolves conflicts                │
    │     - Plans update/merge/skip decisions     │
    │                                              │
    │ 6.  nodePersistFRIntrinsicUpdate            │
    │     - Apply planned updates to FR           │
    │     - Log changes to FROverallUpdateLog     │
    │                                              │
    │ 7.  nodeExtractFineGrainedFeeds             │
    │     - LLM extracts feeds across dimensions  │
    │     - Personality, Interaction,             │
    │       Procedural, Memory dimensions         │
    │     - Returns list of ExtractedFeed         │
    │                                              │
    │ 8.  nodePlanFineGrainedFeedUpsert           │
    │     - Recall existing feeds via vectors     │
    │     - LLM compares old vs new               │
    │     - Decides: add / update / skip / conflict│
    │                                              │
    │ 9.  nodePersistFineGrainedFeedUpsert        │
    │     - Execute add/update operations         │
    │     - Create conflict records if needed     │
    │     - Generate embeddings for new feeds     │
    │                                              │
    │ 10. nodeBuildFRBuildingGraphOutput          │
    │     - Aggregate all results                 │
    │     - Build status summary                  │
    │     - Collect warnings and errors           │
    │                                              │
    │ 11. nodeGenerateFRBuildingReport            │
    │     - LLM generates human-readable report   │
    │     - Persist to FRBuildingGraphReport      │
    │     - Return markdown report text           │
    └──────────────────────────────────────────────┘
        │
        ▼
Return (status, message, fr_building_report, logs, warnings, errors)
        │
        ▼
sendCard2OpenId() — success/failure notification + report card
```

---

## 5. LangGraph Pipeline Design

### 5.1 ConversationGraph

**Graph Structure:**
```
START → nodeLoadFRAndPersona → ┬→ nodeRecallFeedsFromDB ─┬→ nodeCallLLM → END
                               └→ nodeBuildAndTrimMessage ┘
```

**State Schema:** `ConversationGraphState` extends `MessagesState` with:
- `request`: Input request (user_id, fr_id, messages_received)
- `figure_persona`: Built persona markdown
- `recalled_procedural_info_feeds`, `recalled_memory_feeds`: Vector recall results
- `conversation_summary`: Rolling summary of trimmed messages
- `llm_output`: Final LLM response (messages_to_send, reasoning_content)

**Checkpointer:** Uses `PostgresSaver` (async) for short-term memory persistence. Each conversation thread is identified by `thread_id = str(fr_id)`, enabling conversation continuity across sessions.

**Singleton Pattern:** `getConversationGraph()` uses double-checked locking pattern with `asyncio.Lock` to ensure only one graph instance exists per process.

### 5.2 FRBuildingGraph

**Graph Structure:** Sequential 11-node pipeline (described in section 4.2).

**Concurrency Control:** Uses `asyncio.Lock` with explicit `locked()` check before acquisition. If another build is in progress, raises `RuntimeError("FRBuildingGraph is running")`. The caller in `menu.py` catches this and shows a "please wait" message.

**No Checkpointer:** Unlike ConversationGraph, FRBuildingGraph does not use a checkpointer because each build is a one-shot operation that doesn't need cross-session state persistence.

---

## 6. Database Design

### 6.1 Entity-Relationship Overview

```
User (1) ──────────< (N) FigureAndRelation (1) >────────── (N) FineGrainedFeed
                          │                                        │
                          │                                        │
                          ├──< OriginalSource                       ├── FineGrainedFeedConflict
                          ├──< FROverallUpdateLog                   └── embedding (1024-dim HNSW)
                          ├──< FRBuildingGraphReport
                          └──< Knowledge

Knowledge ─── embedding (1024-dim HNSW)
```

### 6.2 Core Models

#### User
- `id`: Primary key
- `username`: Unique username
- `nickname`: Display name
- `gender`: Enum (male/female/other)
- `mbti`: Optional MBTI type (16 types)
- `email`: Unique email
- `password_hash`: bcrypt hashed password
- `lark_open_id`: Optional Lark/Feishu binding
- `created_at`, `updated_at`: Timestamps

#### FigureAndRelation (FR)
- `id`: Primary key
- `user_id`: Foreign key to User
- `figure_name`: Name of the figure
- `figure_role`: Enum (family/friend/mentor/colleague/partner/public_figure/self)
- `figure_mbti`: Figure's MBTI
- `figure_birthday`, `figure_occupation`, `figure_education`, `figure_residence`, `figure_hometown`, `figure_appearance`: Intrinsic fields
- `figure_likes`, `figure_dislikes`: JSONB arrays
- `words_figure2user`, `words_user2figure`: JSONB arrays
- `exact_relation`: Text description of relationship
- `latest_overall_update_log_id`: Tracks most recent update
- `is_deleted`: Soft delete flag

#### FineGrainedFeed
- `id`: Primary key
- `fr_id`: Foreign key to FigureAndRelation
- `original_source_id`: Source tracking
- `dimension`: Enum (PERSONALITY/INTERACTION_STYLE/PROCEDURAL_INFO/MEMORY)
- `sub_dimension`: Optional sub-categorization
- `confidence`: Enum (VERBATIM/ARTIFACT/IMPRESSION)
- `content`: Text content
- `embedding`: 1024-dim vector (pgvector, HNSW indexed)
- `embedding_model_name`: Model identifier for embedding versioning

#### OriginalSource
- `id`: Primary key
- `fr_id`: Foreign key
- `type`: Enum (14 types: CHAT/EMAIL/LETTER/DIARY/PHOTO/etc.)
- `confidence`: Enum
- `included_dimensions`: JSONB array of dimensions covered
- `approx_date`: Optional date approximation
- `content`: Raw source text

#### FineGrainedFeedConflict
- `id`: Primary key
- `fr_id`: Foreign key
- `dimension`: Which dimension has conflict
- `feed_ids`: JSONB array of conflicting feed IDs
- `old_value`, `new_value`: Conflicting values
- `conflict_detail`: LLM-generated conflict analysis
- `status`: Enum (PENDING/RESOLVED_KEEP_OLD/RESOLVED_ACCEPT_NEW/RESOLVED_MERGE/RESOLVED_REWRITE)

### 6.3 Vector Indexing

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- FineGrainedFeed embedding (1024 dimensions)
CREATE INDEX IF NOT EXISTS idx_fgf_embedding 
ON fine_grained_feeds 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 200);

-- Knowledge embedding (1024 dimensions)
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding 
ON knowledge 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 200);
```

**HNSW Parameters:**
- `m = 16`: Number of bi-directional links per layer (higher = better recall, more memory)
- `ef_construction = 200`: Size of dynamic candidate list during construction (higher = better quality, slower build)

---

## 7. LLM Integration

### 7.1 Dual API Architecture

The system supports two LLM API patterns:

**Ark SDK (Native):**
- Used for: Conversation generation, FR building, embeddings
- Client: `volcengine-python-sdk[ark]`
- Key file: `src/agents/ark.py`
- Features: Native multimodal support, responses API with reasoning

**ChatOpenAI (LangChain Adapter):**
- Used for: Field comparison, preprocessing, report generation
- Client: `langchain-openai`
- Key file: `src/agents/llm.py`
- Features: Standard ChatOpenAI interface, compatible with Ark endpoints

### 7.2 Model Configuration

| Environment Variable | Purpose | Typical Value |
|---------------------|---------|---------------|
| `LITE_MODEL` | Primary model for conversation | doubao-2.0-lite-xxx |
| `MINI_MODEL` | Lightweight model for summarization | doubao-2.0-mini-xxx |
| `EMBEDDING_MODEL` | Embedding model endpoint | multimodal-embedding-xxx |
| `ARK_BASE_URL` | Ark API base URL | https://ark.cn-beijing.volces.com/api/v3 |
| `ARK_API_KEY` | Ark API authentication key | (secret) |

### 7.3 Model Selection Strategy

- **Conversation (nodeCallLLM)**: Uses Ark Responses API with `reasoning_effort: "medium"` and `temperature: 1.0`. Supports structured JSON output for `messages_to_send`.
- **Summarization (nodeBuildAndTrimMessage)**: Uses MINI_MODEL with `reasoning_effort: "low"` and `temperature: 0` for deterministic rolling summaries.
- **FR Preprocessing (nodePreprocessInput)**: Uses LITE_MODEL via ChatOpenAI with `temperature: 0` for consistent text classification.
- **Field Comparison (_compareFieldViaLLM)**: Uses prepareLLM with `temperature: 0` for deterministic conflict resolution.
- **Feed Extraction (nodeExtractFineGrainedFeeds)**: Uses LITE_MODEL with role-specific prompt recipes.
- **Feed Upsert Planning (nodePlanFineGrainedFeedUpsert)**: Uses LITE_MODEL for semantic comparison of old vs new feeds.
- **Report Generation (nodeGenerateFRBuildingReport)**: Uses LITE_MODEL with `temperature: 0` for structured markdown output.

### 7.4 Retry Strategy

The `ainvokeJsonWithRetry` function in `src/utils/index.py` implements:
- **Max retries**: 2
- **Retry conditions**: JSON parse failure
- **Error repair**: Attempts to fix common JSON issues (trailing commas, missing brackets) before retry
- **Fallback**: Returns partial results on final failure with error log

---

## 8. Lark Bot Integration

### 8.1 WebSocket Connection Lifecycle

```
startLarkService()
    ├── preconfig() — load .env, configure logging
    ├── initDatabaseIfNeeded() — create tables + extensions
    └── startLarkWebSocketServer(messageHandler)
            │
            ├── Lark WebSocket client connects to Lark open API
            ├── Registers P2ImMessageReceiveV1 event handler
            └── Event loop starts
                    │
                    ├── On message: messageAdapter → messageHandler
                    ├── On disconnect: exponential backoff reconnection
                    └── On shutdown: graceful disconnect
```

### 8.2 Message Adapter

The `messageAdapter()` function handles different message types:
- **Text messages**: Extracts `content.text` directly
- **Image messages**: Extracts `image_url` for potential multimodal processing
- **File messages**: Extracts `file_key` and file metadata
- **Unknown types**: Logs warning, returns None (message dropped)

### 8.3 Card-Based Responses

The system uses Lark interactive cards for structured responses:
- **Success notifications**: Green theme with checkmark
- **Error notifications**: Red theme with error details
- **Info notifications**: Blue/yellow theme based on context
- **Menu cards**: Turquoise theme with formatted command list
- **Report cards**: Violet theme for FR building reports

Card templates are loaded from the Lark Card Builder platform via `LARK_CARD_TEMPLATE_ID` environment variable.

---

## 9. CLI Architecture

### 9.1 Command Tree

```
immortality
├── doctor                    # System health check (6 items)
│                              #   - Python version >= 3.11
│                              #   - .env file existence
│                              #   - 46 required env keys
│                              #   - Dependencies installed
│                              #   - Database connectivity
│                              #   - Output: pass/fail + guidance
├── setup                     # Interactive environment setup
│                              #   - Docker mode: auto PostgreSQL setup
│                              #   - Manual mode: user-input credentials
│                              #   - Configures .env from template
│                              #   - Initializes database tables
├── auth
│   ├── login                 # Username/email + password
│   ├── register              # Interactive (questionary for Gender)
│   ├── logout                # Clear session.json
│   ├── whoami                # Display current user info
│   ├── modify-password       # Change password
│   └── bind-lark             # Bind Lark open_id to account
├── fr
│   ├── add                   # Create new FigureAndRelation
│   ├── list                  # List all FRs for user
│   ├── show                  # Display full FR context (markdown)
│   └── sync-feeds            # Sync feeds to FR core fields
├── lark-service
│   └── start                 # Start Lark bot (doctor check first)
└── logs                      # Tail application logs
    └── --date YYYYMMDD       # Filter by date
```

### 9.2 Output Modes

All commands support `--json` flag for programmatic consumption:
- **Human mode**: Colored output with tables, markdown rendering, ANSI formatting
- **JSON mode**: Raw JSON output of the full service response, suitable for piping

---

## 10. Security Architecture

### 10.1 Authentication

- **JWT tokens**: Generated via `python-jose[cryptography]`, signed with `LOGIN_SECRET`
- **Password hashing**: bcrypt via `bcrypt` library
- **Session persistence**: Tokens stored in `~/.immortality/session.json` with file permissions
- **Token expiry**: Validated by `getUserIdFromLocalSession()`, clears session on expiry

### 10.2 Authorization

- **FR ownership**: Every FR operation validates `user_id` ownership via `checkFigureAndRelationOwnership()`
- **Original source ownership**: `checkOriginalSourceOwnership()` ensures users can only access their own data
- **Feed scope**: All feed operations are scoped to `fr_id` belonging to the authenticated user
- **Lark binding**: `userBindLark()` establishes the user-to-open_id mapping for bot access

### 10.3 Data Protection

- **Sensitive data filtering**: Persona display (`/show_persona`) filters sensitive fields based on the requesting user's relationship to the figure
- **Soft deletes**: FRs, feeds, and original sources use `is_deleted` flag instead of hard deletes
- **Update logging**: All FR intrinsic field changes are logged to `FROverallUpdateLog` for audit trail

---

## 11. Performance Considerations

### 11.1 Connection Pooling

The database engine factory in `src/database/index.py` configures:
- `pool_size`: Number of persistent connections
- `max_overflow`: Additional connections allowed beyond pool_size
- `pool_pre_ping`: Connection health check before use
- `pool_recycle`: Connection lifetime before recycling

### 11.2 Async Event Loop

The Lark integration uses a single persistent event loop in a daemon thread:
- Avoids repeated loop creation/destruction
- Prevents "connection is closed" errors from stale connections
- Uses `asyncio.run_coroutine_threadsafe()` for thread-safe scheduling

### 11.3 Message Batching

Messages are batched with configurable delay (`WAITING_SECONDS_FOR_CONVERSATION`, default 15s):
- Reduces API calls to LLM
- Allows multi-message context to be processed together
- Each new message resets the timer for that user

### 11.4 Vector Search Optimization

- HNSW index on embedding columns for O(log N) approximate nearest neighbor search
- Confidence weighting reduces noise from low-confidence feeds
- Exponential time decay (`timeDecay()`) ensures recent information is prioritized
- Vector candidate limit (`VECTOR_CANDIDATES`) prevents excessive DB load

---

## 12. Error Handling Strategy

### 12.1 Layered Error Handling

```
Layer 1: CLI (CLIError + KeyboardInterrupt) → exit codes
Layer 2: Lark Integration (try/except per handler) → error cards
Layer 3: LangGraph Nodes (try/except per node) → warnings/errors in state
Layer 4: LLM Calls (ainvokeJsonWithRetry) → partial results on failure
Layer 5: Service Layer (status codes + messages) → caller decides
```

### 12.2 Status Code Convention

All service functions return `{"status": int, "message": str}`:
- `200`: Success
- `-1` to `-12`: Specific error codes with descriptive messages
- Negative codes allow callers to programmatically distinguish error types

### 12.3 Logging Strategy

- Application logs: `~/.immortality/logs/app-YYYYMMDD.log`
- Logger hierarchy: module-level loggers with `logging.getLogger(__name__)`
- Log levels: DEBUG (development), INFO (key operations), WARNING (recoverable), ERROR (failures)

---

## 13. Testing Architecture

### 13.1 Test Structure

```
tests/
├── test_integration.py                        # Integration test placeholders
├── cruds/
│   ├── user.py                                # User service manual tests
│   ├── figure_and_relation.py                 # FR service manual tests
│   ├── fine_grained_feed.py                   # Feed service manual tests
│   └── knowledge.py                           # Knowledge service manual tests
├── graphs/
│   ├── ConversationGraph.py                   # Conversation graph manual test
│   ├── ConversationGraph/
│   │   └── test_coherence.py                  # Coherence tests (pytest)
│   └── FRBuildingGraph.py                     # FR building graph manual test
└── channels/
    └── lark/
        └── test_websocket.py                  # WebSocket tests (pytest)
```

### 13.2 Test Patterns

**Manual tests** (`if __name__ == "__main__"`): Designed for development-time validation with real database connections and API calls. These are functional integration tests.

**Pytest tests**: Automated unit/integration tests with mocking:
- `test_coherence.py`: Tests conversation coherence across 5/10/20 turns with 6 role types
- `test_websocket.py`: Tests WebSocket connect/disconnect/reconnect with `unittest.mock`

---

## 14. Build and Deployment

### 14.1 Build System

- **Package manager**: uv (fast Rust-based pip alternative)
- **Build backend**: setuptools
- **Python requirement**: >= 3.11
- **Entry point**: `immortality` CLI command (defined in pyproject.toml)

### 14.2 Docker Deployment

```yaml
# docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: heartcompass
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
  app:
    build: .
    depends_on: [db]
    healthcheck:
      test: pg_isready + vector extension check
```

### 14.3 Environment Configuration

44 required environment variables managed via `~/.immortality/.env`:
- Database connection: `DATABASE_URI`, `CHECKPOINT_DATABASE_URI`
- Authentication: `ALGORITHM`, `LOGIN_SECRET`
- LLM: `ARK_BASE_URL`, `ARK_API_KEY`, model endpoints
- Embeddings: `EMBEDDING_MODEL_NAME`, `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`
- Lark: `LARK_APP_ID`, `LARK_APP_SECRET`, `LARK_CARD_TEMPLATE_ID`
- FR Building: 14 prompt URLs for different stages and roles
- Sync: 8 configuration flags for feed-to-core synchronization
- Tuning: `TOP_K_*`, `VECTOR_CANDIDATES`, `HALF_LIFE_DAYS`, etc.

### 14.4 Database Initialization

`initDatabaseIfNeeded()` in `src/database/models.py`:
1. Creates pgvector extension if not exists
2. Creates all tables (SQLAlchemy `Base.metadata.create_all`)
3. Creates HNSW indexes on embedding columns
4. Creates `immortality_checkpoint` database for LangGraph checkpointer

---

## Appendix A: Dependency Graph

```
pyproject.toml
├── httpx >= 0.28.1
├── alembic >= 1.18.3
├── bcrypt >= 5.0.0
├── python-jose[cryptography] >= 3.5.0
├── dotenv >= 0.9.9
├── sqlalchemy >= 2.0.46
├── langchain >= 1.2.10
├── langgraph >= 1.0.10
├── langchain-openai >= 1.1.9
├── requests >= 2.32.0
├── pgvector >= 0.3.6
├── volcengine-python-sdk[ark] >= 5.0.9
├── aiohttp >= 3.13.3
├── psycopg-binary >= 3.3.3
├── psycopg >= 3.3.3
├── langgraph-checkpoint-postgres >= 3.0.4
├── langgraph-cli[inmem] == 0.4.5
├── hupper >= 1.12.1
├── lark-oapi >= 1.5.3
├── langgraph-api < 0.5.0
├── protobuf < 6
├── vikingdb-python-sdk >= 0.1.15
├── tabulate >= 0.9.0
├── questionary >= 2.1.0
└── rich >= 14.2.0
```

## Appendix B: File Size Summary

| Module | Files | Total Lines |
|--------|-------|-------------|
| CLI | 8 | ~1,860 |
| Database | 4 | ~900 |
| Agents (Core) | 7 | ~820 |
| ConversationGraph | 3 | ~810 |
| FRBuildingGraph | 3 | ~1,680 |
| Lark Channel | 8 | ~1,330 |
| Services | 4 | ~2,440 |
| Utils | 2 | ~240 |
| Tests | 8 | ~700 |
| **Total** | **48** | **~10,780** |

---

*Architecture document maintained by Haojie Hu (Jackey0903). Last updated 2026-06-28.*
