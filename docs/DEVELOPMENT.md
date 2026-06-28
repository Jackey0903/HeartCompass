# HeartCompass Development Guide

**Author:** Haojie Hu (Jackey0903)  
**Date:** 2026-06-28  
**Version:** 1.0.0

---

## Table of Contents

1. [Development Environment Setup](#1-development-environment-setup)
2. [Project Structure Walkthrough](#2-project-structure-walkthrough)
3. [Coding Conventions](#3-coding-conventions)
4. [Adding New Features](#4-adding-new-features)
5. [Working with LangGraph Pipelines](#5-working-with-langgraph-pipelines)
6. [Working with the Database](#6-working-with-the-database)
7. [Working with LLM Integrations](#7-working-with-llm-integrations)
8. [Working with Lark Bot Features](#8-working-with-lark-bot-features)
9. [Testing Guide](#9-testing-guide)
10. [Debugging Techniques](#10-debugging-techniques)
11. [Common Development Tasks](#11-common-development-tasks)
12. [Code Review Checklist](#12-code-review-checklist)
13. [Release Process](#13-release-process)

---

## 1. Development Environment Setup

### 1.1 Quick Setup

```bash
# Clone repository
git clone https://github.com/Jackey0903/HeartCompass.git
cd HeartCompass

# Create virtual environment and install
uv sync
uv pip install -e .

# Set up local environment
cp src/cli/assets/.env.example ~/.immortality/.env
# Edit ~/.immortality/.env with your development credentials

# Initialize the database
uv run python -c "from src.database.models import initDatabaseIfNeeded; initDatabaseIfNeeded()"

# Verify everything works
uv run immortality doctor
```

### 1.2 IDE Configuration

**VS Code (Recommended):**
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.formatting.provider": "black",
    "python.analysis.typeCheckingMode": "basic",
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

### 1.3 Pre-commit Setup

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 2. Project Structure Walkthrough

### 2.1 Directory Map

```
HeartCompass/
├── src/
│   ├── main.py                          # Application entry point
│   ├── agents/                          # AI/LLM layer
│   │   ├── llm.py                       # LLM initialization
│   │   ├── ark.py                       # Ark SDK client
│   │   ├── embedding.py                 # Vector embeddings
│   │   ├── adapter.py                   # Message conversion
│   │   ├── prompt.py                    # Prompt loading
│   │   ├── types.py                     # LLM response types
│   │   └── graphs/                      # LangGraph pipelines
│   │       ├── checkpointer.py          # State persistence
│   │       ├── ConversationGraph/       # Chat pipeline
│   │       └── FRBuildingGraph/         # Persona building
│   ├── channels/lark/                   # Lark bot integration
│   ├── cli/                             # Command-line interface
│   ├── database/                        # Data access layer
│   ├── services/                        # Business logic
│   └── utils/                           # Shared utilities
├── tests/                               # Test suite
├── scripts/                             # Generation scripts
├── docs/                                # Documentation
├── prompts/                             # LLM system prompts
└── output/                              # Generated outputs
```

### 2.2 Key Files by Responsibility

**Entry Points:**
- `src/main.py` → Lark bot service
- `src/cli/main.py` → CLI commands

**Core Logic:**
- `src/agents/graphs/ConversationGraph/nodes.py` → Conversation nodes
- `src/agents/graphs/FRBuildingGraph/nodes.py` → Persona building nodes
- `src/services/figure_and_relation.py` → FR business logic
- `src/services/fine_grained_feed.py` → Feed management logic

**Integration:**
- `src/channels/lark/websocket.py` → WebSocket server
- `src/channels/lark/integration/index.py` → Message orchestration
- `src/channels/lark/integration/menu.py` → Bot commands

**Data:**
- `src/database/models.py` → All ORM models
- `src/database/enums.py` → All enum types
- `src/database/index.py` → Database engine

### 2.3 Import Patterns

```python
# NEVER do relative imports
# BAD:
from .utils import something

# GOOD:
from src.utils.index import something

# NEVER import from a module that creates side effects at import time
# BAD (creates DB connection pool at import):
from src.database.index import engine

# GOOD (uses lazy initialization):
from src.database.index import session
```

---

## 3. Coding Conventions

### 3.1 Python Style

```python
# Function naming: camelCase for consistency with existing codebase
def getUserByUsername(username: str) -> dict:
    """Get a user by their username."""
    ...

# Variable naming: snake_case for local variables
user_count = len(users)

# Type hints required for all function signatures
async def processMessages(
    user_id: int,
    fr_id: int,
    messages: list[str],
) -> tuple[list[str], str]:
    ...

# Docstrings: concise, explain WHY not WHAT
def filterDuplicatedMessage(message: str, open_id: str) -> bool:
    """Filter exact duplicates within a sliding time window to
    prevent double-processing from Lark SDK edge cases."""
    ...
```

### 3.2 Async/Await Patterns

```python
# Always use async def when calling await
async def my_function():
    result = await some_async_call()
    return result

# Never mix sync and async in the same call chain
# BAD:
def sync_function():
    asyncio.run(async_function())  # creates/destroys event loop

# GOOD:
async def async_entry_point():
    await async_function()

# For thread-safe async from sync context:
loop = _getOrCreateAsyncLoop()
future = asyncio.run_coroutine_threadsafe(coro, loop)
result = future.result(timeout=120)
```

### 3.3 Service Response Pattern

All service functions follow this convention:

```python
def myServiceFunction(param: int) -> dict:
    """
    Returns {"status": int, "message": str, ...}
    
    Status codes:
      200: Success
      -1 to -N: Specific error codes (always negative to distinguish from HTTP)
    """
    if not isinstance(param, int):
        return {"status": -1, "message": "Invalid param"}
    
    # ... business logic ...
    
    return {"status": 200, "message": "Success"}
```

### 3.4 Error Handling

```python
# Service layer: return error dicts
if error:
    return {"status": -1, "message": "Description"}

# CLI layer: raise CLIError for expected errors
raise CLIError("User-friendly message", exit_code=2)

# Graph nodes: append to warnings/errors in state
state["warnings"].append("Non-critical issue")
state["errors"].append("Critical failure")

# LLM calls: use retry wrapper
result = await ainvokeJsonWithRetry(llm, messages, max_retries=2)

# Lark handlers: catch and show error cards
try:
    result = await processMessages(...)
except Exception as e:
    logger.warning(f"Failed: {e}", exc_info=True)
    sendCard2OpenId(open_id, title="Error", content="...")
```

---

## 4. Adding New Features

### 4.1 Adding a New CLI Command

```python
# Step 1: Create command function in src/cli/commands/
def newCommandCLI(args: Namespace) -> int:
    """Description of the command."""
    user_id = getUserIdFromLocalSession()
    # ... implementation ...
    printServiceResInCLI(result, as_json=args.json)
    return 0

# Step 2: Register in parser builder
def registerNewSubparser(subparsers, add_json):
    parser = subparsers.add_parser("new-command", help="Description")
    parser.usage = "immortality new-command [options]"
    add_json(parser)
    parser.add_argument("--option", help="Option description")
    parser.set_defaults(func=newCommandCLI)

# Step 3: Register in main parser (src/cli/main.py:parserBuilder)
registerNewSubparser(subparsers, add_json)
```

### 4.2 Adding a New Service

```python
# src/services/new_service.py
import logging
from src.database.index import session
from src.database.models import SomeModel

logger = logging.getLogger(__name__)

def doSomething(param: int) -> dict:
    """Do something useful."""
    if not isinstance(param, int):
        return {"status": -1, "message": "Invalid param"}
    
    with session() as db:
        # ... database operations ...
        pass
    
    return {"status": 200, "message": "Success"}
```

### 4.3 Adding a New Database Model

```python
# Step 1: Define model in src/database/models.py
class NewModel(Base, SerializableMixin):
    __tablename__ = "new_models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Step 2: Generate migration
# cd alembic && alembic revision --autogenerate -m "add new_model"

# Step 3: Apply migration
# alembic upgrade head
```

---

## 5. Working with LangGraph Pipelines

### 5.1 Creating a New Graph

```python
# src/agents/graphs/NewGraph/state.py
class NewGraphState(TypedDict, total=False):
    request: dict
    result: str | None
    logs: list[dict]

class NewGraphInput(TypedDict, total=False):
    request: dict

class NewGraphOutput(TypedDict, total=False):
    result: str

# src/agents/graphs/NewGraph/nodes.py
def nodeStep1(state: NewGraphState) -> dict:
    """First processing step."""
    return {"logs": [{"step": "step1", "status": "ok"}]}

async def nodeStep2(state: NewGraphState) -> dict:
    """Second processing step (async)."""
    result = await some_async_operation()
    return {"result": result}

# src/agents/graphs/NewGraph/graph.py
from langgraph.graph import StateGraph, START, END

def buildNewGraph() -> CompiledStateGraph:
    graph = StateGraph(
        state_schema=NewGraphState,
        input_schema=NewGraphInput,
        output_schema=NewGraphOutput,
    )
    graph.add_node("step1", nodeStep1)
    graph.add_node("step2", nodeStep2)
    graph.add_edge(START, "step1")
    graph.add_edge("step1", "step2")
    graph.add_edge("step2", END)
    return graph.compile()
```

### 5.2 Node Implementation Guidelines

```python
async def nodeExample(state: SomeState) -> dict:
    """
    Node description: what it does and what it returns.
    
    Input from state:
        - request.user_id: int
        - request.content: str
    
    Returns:
        - processed_result: str
        - warnings: list[str] (if issues found)
        - logs: list[dict] (execution log)
    """
    logger.info("nodeExample is called")
    
    # Extract and validate inputs
    request = state.get("request") or {}
    user_id = request.get("user_id")
    if not isinstance(user_id, int):
        logger.error("Invalid user_id")
        raise ValueError("Invalid request.user_id")
    
    # Accumulate warnings (don't overwrite existing)
    warnings = list(state.get("warnings") or [])
    logs = list(state.get("logs") or [])
    
    try:
        # Core logic
        result = await do_processing()
        
        logs.append({
            "step": "nodeExample",
            "status": "ok",
            "detail": "Processing completed",
            "data": {"result_length": len(result)},
        })
        
        return {
            "processed_result": result,
            "warnings": warnings,
            "logs": logs,
        }
    except Exception as e:
        warning_msg = f"Processing failed: {str(e)}"
        logger.warning(warning_msg)
        warnings.append(warning_msg)
        return {
            "processed_result": None,
            "warnings": warnings,
            "logs": logs,
        }
```

### 5.3 State Field Naming

- Use descriptive `snake_case` names
- Prefer specific names over generic ones: `recalled_memory_feeds` not `feeds`
- Use `Annotated[list, _mergeUniqueList]` for fields written by parallel branches
- Always add new fields to both the state TypedDict and the relevant node returns

---

## 6. Working with the Database

### 6.1 Session Management

```python
# Always use context manager
from src.database.index import session

def my_operation():
    with session() as db:
        # Queries here
        result = db.query(SomeModel).filter(...).first()
        # db.commit() is called automatically on success
        # db.rollback() is called automatically on exception
```

### 6.2 Query Patterns

```python
# Simple query
user = db.query(User).filter(User.id == user_id).first()

# Filter with soft delete
feeds = db.query(FineGrainedFeed).filter(
    FineGrainedFeed.fr_id == fr_id,
    FineGrainedFeed.is_deleted == False,
).all()

# Vector similarity search
from pgvector.sqlalchemy import Vector
distance = FineGrainedFeed.embedding.cosine_distance(query_vector)
results = db.query(
    FineGrainedFeed, 
    distance.label("distance")
).filter(
    FineGrainedFeed.fr_id == fr_id,
    FineGrainedFeed.is_deleted == False,
).order_by(
    distance.asc()
).limit(top_k).all()

# Bulk insert
db.add_all([instance1, instance2, instance3])
db.commit()

# Update
obj = db.query(Model).filter(Model.id == id).first()
if obj:
    obj.field = new_value
    db.commit()
```

### 6.3 Ownership Verification

```python
# Always verify ownership before operating on FR data
fr = checkFigureAndRelationOwnership(
    db=db,
    user_id=user_id,
    fr_id=fr_id,
)
if fr is None:
    return {"status": -8, "message": "FigureAndRelation not found"}
```

### 6.4 Working with Enums

```python
from src.database.enums import FineGrainedFeedDimension, parseEnum

# Using enums in queries
feeds = db.query(FineGrainedFeed).filter(
    FineGrainedFeed.dimension == FineGrainedFeedDimension.MEMORY
).all()

# Parsing enum from string
dimension = parseEnum(FineGrainedFeedDimension, "memory")
if not isinstance(dimension, FineGrainedFeedDimension):
    return {"status": -1, "message": "Invalid dimension"}

# Enums as JSONB in database
# PostgreSQL stores enum values as strings in JSONB columns
```

---

## 7. Working with LLM Integrations

### 7.1 Calling the LLM

```python
from src.agents.llm import prepareLLM
from langchain_core.messages import SystemMessage, HumanMessage

# Standard LLM call
llm = prepareLLM(
    "LITE_MODEL",
    options={
        "temperature": 0.7,
        "reasoning_effort": "medium",
    },
)
response = await llm.ainvoke([
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="User query here."),
])

# With JSON output parsing and retry
from src.utils.index import ainvokeJsonWithRetry
result = await ainvokeJsonWithRetry(
    llm,
    messages,
    max_retries=2,
)
```

### 7.2 Calling Embeddings

```python
from src.agents.embedding import vectorizeText, vectorizeImage, vectorizeMixed

# Text embedding
vector = await vectorizeText("Some text to vectorize")

# Image embedding
vector = await vectorizeImage("https://example.com/image.jpg")

# Mixed embedding (text + images)
vector = await vectorizeMixed(
    text=["text1", "text2"],
    image_url=["https://example.com/img1.jpg"],
)
```

### 7.3 Loading Prompts

```python
from src.agents.prompt import getPrompt

# Load prompt from Prompt Minder URL
prompt_text = await getPrompt(
    prompt_minder_url=os.getenv("SOME_PROMPT_URL"),
    variables={"key": "value"},
)
if not prompt_text:
    logger.error("Failed to load prompt")
    raise ValueError("Prompt not found")
```

### 7.4 Using Ark SDK Directly

```python
from src.agents.ark import arkClient
import os

client = arkClient()
response = await client.responses.create(
    model=os.getenv("LITE_MODEL"),
    input=[
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User message"},
    ],
    reasoning={"effort": "medium"},
    text={"format": {"type": "json_object"}},
)
```

---

## 8. Working with Lark Bot Features

### 8.1 Adding a New Bot Command

```python
# In src/channels/lark/integration/menu.py

# Step 1: Create command handler
def handleNewCommand(message: str, open_id: str) -> bool:
    """Handle /new_command <arg>"""
    import re
    pattern = r"^/new_command(?:\s+(.+))?$"
    match = re.match(pattern, message)
    if not match:
        return False
    
    arg = (match.group(1) or "").strip()
    # ... command logic ...
    
    sendCard2OpenId(
        open_id=open_id,
        title="Command Result",
        content=f"Processed: {arg}",
        theme="blue",
    )
    return True

# Step 2: Register in handleMenuCommand()
def handleMenuCommand(message: str, open_id: str) -> bool:
    handlers = [
        showMenuLark,
        listAvailableFRsLark,
        switchFRLark,
        clearCurrentRelationChainLark,
        showFRLark,
        buildPersonaLark,
        handleNewCommand,  # Add here
    ]
    for handler in handlers:
        try:
            if handler(message, open_id):
                return True
        except Exception as e:
            logger.warning(f"Handler failed: {e}")
    return False
```

### 8.2 Sending Messages

```python
from src.channels.lark.integration.utils import sendText2OpenId, sendCard2OpenId

# Send text message
sendText2OpenId(open_id="ou_xxxx", text="Hello from HeartCompass!")

# Send card message
sendCard2OpenId(
    open_id="ou_xxxx",
    title="Notification Title",
    content="Message body with **markdown** support",
    theme="green",  # green, red, yellow, blue, turquoise, violet
)
```

---

## 9. Testing Guide

### 9.1 Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/graphs/ConversationGraph/test_coherence.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run manual tests (standalone scripts)
uv run python tests/cruds/user.py
uv run python tests/cruds/figure_and_relation.py
```

### 9.2 Writing Tests

```python
import pytest
from unittest.mock import patch, MagicMock

# Async test
@pytest.mark.asyncio
async def test_conversation_with_mocked_llm():
    """Test conversation flow with mocked LLM response."""
    # Arrange
    mock_llm = MagicMock()
    mock_llm.ainvoke.return_value = MagicMock(
        content='{"messages_to_send": ["Hello!"]}'
    )
    
    with patch("src.agents.llm.prepareLLM", return_value=mock_llm):
        # Act
        result = await processMessages(
            user_id=1,
            fr_id=1,
            messages=["Hi"],
        )
        
        # Assert
        assert len(result[0]) > 0
        assert "Hello" in result[0][0]

# Parametrized test
@pytest.mark.parametrize("role", [
    "family", "friend", "mentor", "colleague", "partner"
])
@pytest.mark.asyncio
async def test_role_specific_responses(role):
    """Test that each role produces contextually appropriate responses."""
    ...
```

### 9.3 Mocking Guidelines

```python
# Mock database session
@patch("src.database.index.session")
def test_with_mock_db(mock_session):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    ...

# Mock LLM
@patch("src.agents.llm.prepareLLM")
def test_with_mock_llm(mock_prepare_llm):
    mock_llm = MagicMock()
    mock_prepare_llm.return_value = mock_llm
    ...

# Mock embeddings
@patch("src.agents.embedding.vectorizeText")
async def test_with_mock_embeddings(mock_vectorize):
    mock_vectorize.return_value = [0.1] * 1024
    ...

# Mock external API
@patch("src.channels.lark.client.larkClient")
def test_with_mock_lark(mock_lark_client):
    ...
```

---

## 10. Debugging Techniques

### 10.1 Logging

```python
import logging
logger = logging.getLogger(__name__)

# Levels in order of severity
logger.debug("Detailed diagnostic info")     # Development only
logger.info("Key operation completed")       # Normal operation
logger.warning("Something unexpected")       # Recoverable issue  
logger.error("Operation failed", exc_info=True)  # Failure with traceback
```

### 10.2 Viewing Logs

```bash
# Live tail of today's logs
uv run immortality logs

# Filter for specific module
grep "ConversationGraph\|FRBuildingGraph" ~/.immortality/logs/app-$(date +%Y%m%d).log

# Filter for errors and warnings
grep -E "ERROR|WARNING" ~/.immortality/logs/app-*.log | tail -50

# Track specific FR conversation
grep "fr_id.*=.*5" ~/.immortality/logs/app-$(date +%Y%m%d).log
```

### 10.3 Graph State Inspection

```python
# Add inspection node to graph for debugging
def nodeInspectState(state: ConversationGraphState) -> dict:
    """Debug node: log full state."""
    import json
    safe_state = {k: v for k, v in state.items() 
                  if k not in ['messages']}
    logger.debug(f"State: {json.dumps(safe_state, default=str, indent=2)}")
    return {}

# Add to graph temporarily
graph.add_node("inspect", nodeInspectState)
graph.add_edge("nodeLoadFRAndPersona", "inspect")
graph.add_edge("inspect", "nodeRecallFeedsFromDB")
```

### 10.4 Database Inspection

```bash
# Connect directly to database
psql -U immortality -h 127.0.0.1 -d immortality

# Useful queries
SELECT id, figure_name, figure_role FROM figure_and_relations WHERE is_deleted = false;
SELECT dimension, COUNT(*) FROM fine_grained_feeds WHERE is_deleted = false GROUP BY dimension;
SELECT * FROM fr_overall_update_logs ORDER BY created_at DESC LIMIT 10;

# Vector index stats
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'fine_grained_feeds';
```

---

## 11. Common Development Tasks

### 11.1 Adding a New Persona Dimension

```python
# Step 1: Add enum value in src/database/enums.py
class FineGrainedFeedDimension(Enum):
    PERSONALITY = "personality"
    INTERACTION_STYLE = "interaction_style"
    PROCEDURAL_INFO = "procedural_info"
    MEMORY = "memory"
    NEW_DIMENSION = "new_dimension"  # Add here

# Step 2: Add recall configuration
TOP_K_NEW_DIMENSION_FEEDS_FOR_CONVERSATION = os.getenv(
    "TOP_K_NEW_DIMENSION_FEEDS_FOR_CONVERSATION", "5"
)

# Step 3: Add recall scope in ConversationGraph nodes.py
recall_scopes = [
    {"scope": FineGrainedFeedDimension.PROCEDURAL_INFO, "top_k": K_PROCEDURAL_INFO},
    {"scope": FineGrainedFeedDimension.MEMORY, "top_k": K_MEMORY},
    {"scope": FineGrainedFeedDimension.NEW_DIMENSION, "top_k": K_NEW_DIMENSION},  # Add
]

# Step 4: Add extraction prompt for FRBuildingGraph
# Add prompt URL env var: FR_BUILDING_NEW_DIMENSION
# Add extraction logic in nodeExtractFineGrainedFeeds
```

### 11.2 Adding a New Figure Role

```python
# Step 1: Add enum value in src/database/enums.py
class FigureRole(Enum):
    FAMILY = "family"
    FRIEND = "friend"
    MENTOR = "mentor"
    COLLEAGUE = "colleague"
    PARTNER = "partner"
    PUBLIC_FIGURE = "public_figure"
    SELF = "self"
    NEW_ROLE = "new_role"  # Add here

# Step 2: Add formality level in src/agents/prompts/conversation.py
FORMALITY_LEVELS = {
    'family': 0.3, 'friend': 0.4, 'mentor': 0.5,
    'colleague': 0.6, 'partner': 0.4, 'new_role': 0.5,  # Add
}

# Step 3: Create role recipe prompt
# Create prompts/recipes/by_role/new_role.md

# Step 4: Add prompt URL env var: FR_BUILDING_NEW_ROLE
```

### 11.3 Updating Dependencies

```bash
# Add new dependency
uv add package-name

# Update all dependencies
uv sync --upgrade

# Update specific package
uv add package-name@latest

# Check for security vulnerabilities
uv pip check
```

---

## 12. Code Review Checklist

### 12.1 Before Submitting Code

- [ ] All Python files pass `py_compile` (no syntax errors)
- [ ] No `//` comments in Python files (use `#` instead)
- [ ] No hardcoded secrets (use environment variables)
- [ ] All new functions have type hints
- [ ] Service functions return `{"status": int, "message": str}` pattern
- [ ] Database operations use context manager `with session() as db:`
- [ ] FR operations verify ownership via `checkFigureAndRelationOwnership()`
- [ ] No `asyncio.run()` in library code (use async/await or thread-safe patterns)
- [ ] Error cases are handled (not silently ignored)
- [ ] Logging includes appropriate level and context

### 12.2 Common Mistakes to Avoid

1. **Forgetting to validate user_id/fr_id types**: Always check `isinstance(id, int)` before using
2. **Modifying state lists in place**: Always create new list: `warnings = list(state.get("warnings") or [])`
3. **Not handling None in state.get()**: Always use `state.get("field") or default_value`
4. **Using f-strings with backslashes**: Extract complex expressions to variables first
5. **Importing from `__init__.py` files**: Import directly from the module file
6. **Creating new event loops**: Use the shared persistent loop via `_runAsync()`

---

## 13. Release Process

### 13.1 Version Numbering

```
MAJOR.MINOR.PATCH
  │     │     └── Bug fixes, minor improvements
  │     └──────── New features (backwards compatible)
  └────────────── Breaking changes
```

### 13.2 Release Checklist

```bash
# 1. Verify all tests pass
uv run pytest tests/ -v

# 2. Run doctor check
uv run immortality doctor

# 3. Check for compilation errors
find src tests -name "*.py" -exec python3 -m py_compile {} \;

# 4. Review changes
git log --oneline origin/main..HEAD

# 5. Update version in pyproject.toml
# Edit: version = "X.Y.Z"

# 6. Create release commit
git add pyproject.toml
git commit -m "chore(release): vX.Y.Z"

# 7. Tag release
git tag -a "vX.Y.Z" -m "Release vX.Y.Z"

# 8. Push
git push origin main
git push origin vX.Y.Z
```

### 13.3 Post-Release

```bash
# Verify deployment
uv run immortality doctor

# Monitor logs for 24 hours
tail -f ~/.immortality/logs/app-$(date +%Y%m%d).log

# Check for error spikes
grep ERROR ~/.immortality/logs/app-$(date +%Y%m%d).log | wc -l
```

---

## Appendix: Quick Reference

### A.1 File Naming

| Module | Pattern | Example |
|--------|---------|---------|
| Services | `snake_case.py` | `figure_and_relation.py` |
| Graph nodes | `nodes.py` | `ConversationGraph/nodes.py` |
| Graph definition | `graph.py` | `ConversationGraph/graph.py` |
| Graph state | `state.py` | `ConversationGraph/state.py` |
| CLI commands | `commands/name.py` | `commands/auth.py` |
| Database | `models.py`, `enums.py` | |
| Utils | `name.py` in `utils/` or `index.py` | |

### A.2 Environment Variable Naming

- Database: `DATABASE_*`, `CHECKPOINT_DATABASE_*`
- Auth: `ALGORITHM`, `LOGIN_SECRET`
- LLM: `ARK_*`, `*_MODEL`
- Embeddings: `EMBEDDING_*`
- Lark: `LARK_*`
- FR Building: `FR_BUILDING_*`
- Sync: `SYNC_*_TO_FR_CORE`
- Tuning: `TOP_K_*`, `SHORT_TERM_*`, `VECTOR_*`, `HALF_LIFE_*`

### A.3 Common Import Paths

```python
# Database
from src.database.index import session
from src.database.models import User, FigureAndRelation, FineGrainedFeed
from src.database.enums import Gender, FigureRole, FineGrainedFeedDimension

# Services
from src.services.user import getUserById, getUserIdByAccessToken
from src.services.figure_and_relation import getFigureAndRelation, buildFigurePersonaMarkdown
from src.services.fine_grained_feed import recallFineGrainedFeeds, addFineGrainedFeed

# LLM
from src.agents.llm import prepareLLM
from src.agents.ark import arkClient
from src.agents.embedding import vectorizeText

# Utils
from src.utils.index import timeDecay, ainvokeJsonWithRetry, checkFigureAndRelationOwnership

# CLI
from src.cli.utils import CLIError, immortalityPrint, printServiceResInCLI
from src.cli.session import loadLocalSession, saveLocalSession
```

---

*Development guide maintained by Haojie Hu (Jackey0903). Last updated 2026-06-28.*
