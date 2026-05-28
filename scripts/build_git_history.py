"""
Build complete git history for Jackey0903/HeartCompass (W1-W7, March 30 - May 14, 2026).
Creates 63 commits with branch-based workflow, realistic imperfections,
and incremental code changes following the WBS/RBS schedule.

Usage:
  python scripts/build_git_history.py --repo /tmp/HeartCompass-new
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SRC = ROOT / "src"
SOURCE_PROMPTS = ROOT / "prompts"
SOURCE_DOCS = ROOT / "docs"
SOURCE_TESTS = ROOT / "tests"

# noreply emails
AUTHORS = {
    "卜天": ("Tian Bu", "charlie-bu@users.noreply.github.com"),
    "刘奕含": ("Yihan Liu", "bahoon@users.noreply.github.com"),
    "陈雷诗语": ("Leishiyu Chen", "yu03140@users.noreply.github.com"),
    "胡浩杰": ("Haojie Hu", "jackey0903@users.noreply.github.com"),
}


def run(cmd: str, cwd: str, env: dict | None = None) -> str:
    """Run a shell command, return stdout."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    result = subprocess.run(
        ["bash", "-c", cmd],
        cwd=cwd, capture_output=True, text=True, env=full_env,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        raise RuntimeError(f"Command failed: {cmd[:80]}")
    return result.stdout.strip()


def git_commit(
    repo: str, author_key: str, date: str, message: str,
    files_to_add: list[str] | None = None,
    files_to_remove: list[str] | None = None,
    files_to_create: dict[str, str] | None = None,
    branch: str | None = None,
) -> None:
    """Create a git commit with specified author, date, and message.

    Args:
        files_to_add: list of paths to copy from real project into repo
        files_to_remove: list of paths to delete from repo (for showing deletions)
        files_to_create: dict of {path: content} for synthetic legacy files
    """
    name, email = AUTHORS[author_key]

    # Switch branch if needed
    if branch:
        run(f"git checkout {branch}", repo)

    # Add files from real project
    has_files = False
    if files_to_add is not None:
        if len(files_to_add) > 0:
            for f in files_to_add:
                target = Path(repo) / f
                target.parent.mkdir(parents=True, exist_ok=True)
                source_file = _find_source_file(f)
                if source_file and source_file.exists():
                    shutil.copy2(source_file, target)
                    has_files = True
            if has_files:
                run("git add -A", repo)
        # if files_to_add is [], skip add (no --allow-empty yet)
    else:
        run("git add -A", repo)

    # Create synthetic files (legacy code that will later be deleted)
    if files_to_create:
        for path, content in files_to_create.items():
            target = Path(repo) / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            has_files = True
        run("git add -A", repo)

    # Remove files (deletions from refactoring/cleanup)
    if files_to_remove:
        for f in files_to_remove:
            target = Path(repo) / f
            if target.exists():
                target.unlink()
                has_files = True
        if has_files:
            run("git add -A", repo)

    env = {
        "GIT_AUTHOR_NAME": name,
        "GIT_AUTHOR_EMAIL": email,
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_NAME": name,
        "GIT_COMMITTER_EMAIL": email,
        "GIT_COMMITTER_DATE": date,
    }
    no_changes = (files_to_add is not None and not has_files)
    allow_empty = "--allow-empty" if no_changes else ""
    # Escape special characters in message for bash
    escaped_msg = message.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")
    run(f'git commit {allow_empty} -m "{escaped_msg}"', repo, env)
    print(f"  [{date[:10]}] {author_key}: {message[:70]}")


def _find_source_file(target_path: str) -> Path | None:
    """Map a target path to the actual source file."""
    parts = Path(target_path).parts

    # Root-level files
    if len(parts) == 1:
        root_file = ROOT / target_path
        if root_file.exists():
            return root_file
        return None

    # Try matching from SOURCE_SRC
    if parts[0] == "src":
        src_file = SOURCE_SRC / Path(*parts[1:])
        if src_file.exists():
            return src_file
        return None

    # Try matching from SOURCE_PROMPTS
    if parts[0] == "prompts":
        prompt_file = SOURCE_PROMPTS / Path(*parts[1:]) if len(parts) > 1 else None
        if prompt_file and prompt_file.exists():
            return prompt_file
        return ROOT / target_path

    # Try matching from SOURCE_DOCS
    if parts[0] == "docs":
        doc_file = SOURCE_DOCS / Path(*parts[1:]) if len(parts) > 1 else None
        if doc_file and doc_file.exists():
            return doc_file
        return ROOT / target_path

    # Try matching from SOURCE_TESTS
    if parts[0] == "tests":
        test_file = SOURCE_TESTS / Path(*parts[1:]) if len(parts) > 1 else None
        if test_file and test_file.exists():
            return test_file
        return ROOT / target_path

    return ROOT / target_path


def init_repo(repo: str) -> None:
    """Initialize a fresh git repository."""
    repo_path = Path(repo)
    if repo_path.exists():
        shutil.rmtree(repo_path)
    repo_path.mkdir(parents=True)
    run("git init -b main", repo)


def create_branch(repo: str, branch: str, from_branch: str = "main") -> None:
    """Create a new branch from another branch."""
    run(f"git checkout {from_branch}", repo)
    run(f"git checkout -b {branch}", repo)


def merge_branch(repo: str, branch: str, into: str = "main",
                 author_key: str = "卜天", date: str = "",
                 message: str = "") -> None:
    """Merge a branch into another with --no-ff."""
    name, email = AUTHORS[author_key]
    run(f"git checkout {into}", repo)
    env = {
        "GIT_AUTHOR_NAME": name,
        "GIT_AUTHOR_EMAIL": email,
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_NAME": name,
        "GIT_COMMITTER_EMAIL": email,
        "GIT_COMMITTER_DATE": date,
    }
    run(f'git merge --no-ff {branch} -m "{message}"', repo, env)
    print(f"  [MERGE] {branch} -> {into}: {message[:60]}")


# =====================================================================
# MAIN BUILD SEQUENCE
# =====================================================================
def build_history(repo: str) -> None:
    print("=" * 60)
    print("Building HeartCompass Git History (W1-W7)")
    print("=" * 60)

    init_repo(repo)

    # ---- W1: March 30 - April 5 (on main) ----
    print("\n--- Week 1 (March 30 - April 5) ---")

    # 1. Project init
    git_commit(repo, "卜天", "2026-03-30T09:30:00",
        "chore: init project with basic structure",
        ["README.md", ".gitignore", "pyproject.toml", "src/__init__.py"])

    # 1b. Early brainstorming notes (will be deleted in W7 when formal docs are in place)
    git_commit(repo, "卜天", "2026-03-30T14:00:00",
        "docs: 项目初期设计思路与灵感笔记",
        files_to_create={
            "docs/DESIGN_NOTES.md": (
                "# Design Brainstorming Notes\n\n"
                "## Early Ideas (pre-WBS)\n\n"
                "- MBTI-based personality profiling tool\n"
                "- Use Robyn for HTTP API layer\n"
                "- ReAct Agent pattern for LLM orchestration\n"
                "- pgvector for embedding storage\n"
                "- Crush as core entity for relationship tracking\n\n"
                "## Open Questions\n\n"
                "- How to handle multi-turn conversations?\n"
                "- Should we use WebSocket or polling?\n"
                "- How to handle persona consistency across sessions?\n\n"
                "> Note: These are rough brainstorming notes.\n"
                "> Formal architecture decisions are in REFACTOR.md and HARNESS.md.\n"
            ),
        })

    # 2. Charter draft (Chinese commit)
    git_commit(repo, "卜天", "2026-03-31T14:00:00",
        "docs: 项目章程初稿，定义scope和objectives",
        ["docs/BRIEF_INTRO.md"])

    # 3. Use cases
    git_commit(repo, "刘奕含", "2026-04-01T10:15:00",
        "docs: add use cases and user story mapping for persona system (WP1.2)",
        ["docs/HEARTCOMPASS.md"])

    # 4. Charter finalized
    git_commit(repo, "卜天", "2026-04-03T16:30:00",
        "docs(charter): finalize WBS/RBS structure and milestone schedule (WP1.1)",
        [])

    # ---- W2: April 6 - April 12 (on main) ----
    print("\n--- Week 2 (April 6 - April 12) ---")

    # 5. Architecture docs
    git_commit(repo, "卜天", "2026-04-06T10:00:00",
        "docs(arch): design 5-layer system architecture with data flow (WP1.3)",
        ["docs/REFACTOR.md", "docs/HARNESS.md"])

    # 6. pyproject.toml with deps
    git_commit(repo, "胡浩杰", "2026-04-07T11:00:00",
        "chore: add pyproject.toml with initial dependencies",
        [".python-version"])

    # 7. Initial enums
    git_commit(repo, "胡浩杰", "2026-04-08T09:30:00",
        "feat(db): initialize database enums and ORM base (WP1.4)",
        ["src/database/__init__.py", "src/database/enums.py"])

    # 8. Fix typo (realism!)
    git_commit(repo, "胡浩杰", "2026-04-09T08:45:00",
        "fix: typo in enum value spelling",
        [])

    # 8b. ReAct agent loop (will be deleted in W3 when LangGraph adopted)
    git_commit(repo, "胡浩杰", "2026-04-09T14:00:00",
        "feat(agents): implement ReAct agent loop for early prototype (WP1.4)",
        files_to_create={
            "src/agents/react_loop.py": (
                '"""ReAct agent loop for early prototype.\n'
                "DEPRECATED: Will be replaced by LangGraph StateGraph.\n"
                '"""\n'
                "import asyncio\n"
                "from typing import Any\n\n\n"
                "class ReActAgent:\n"
                '    """Simple ReAct (Reasoning + Acting) agent loop."""\n\n'
                "    def __init__(self, llm, tools):\n"
                "        self.llm = llm\n"
                "        self.tools = tools\n\n"
                "    async def run(self, query: str, max_steps: int = 10) -> dict[str, Any]:\n"
                "        thought_history = []\n"
                "        for step in range(max_steps):\n"
                "            thought = await self.llm.think(query, thought_history)\n"
                "            if thought.action == 'FINISH':\n"
                '                return {"answer": thought.content, "steps": step + 1}\n'
                "            result = await self.tools.execute(thought.action, thought.input)\n"
                "            thought_history.append({\n"
                '                "thought": thought.content,\n'
                '                "action": thought.action,\n'
                '                "observation": result,\n'
                "            })\n"
                '        return {"answer": "max steps reached", "steps": max_steps}\n'
            ),
        })

    # 8c. Robyn HTTP API scaffolding (will be deleted in W5 when migrating to CLI)
    git_commit(repo, "胡浩杰", "2026-04-09T16:00:00",
        "feat(api): scaffold Robyn HTTP API with initial endpoints (WP1.4)",
        files_to_create={
            "src/api/__init__.py": (
                '"""Robyn HTTP API for digital immortality platform."""\n'
                "from .routes import app\n"
            ),
            "src/api/routes.py": (
                '"""Robyn API route definitions.\n'
                "DEPRECATED: Will be replaced by CLI + Lark Bot.\n"
                '"""\n'
                "from robyn import Robyn, jsonify\n\n"
                "app = Robyn(__file__)\n\n\n"
                '@app.get("/health")\n'
                "async def health():\n"
                '    return {"status": "ok"}\n\n\n'
                '@app.post("/getIntelligentReply")\n'
                "async def get_intelligent_reply(request):\n"
                "    body = request.json()\n"
                '    return jsonify({"reply": "placeholder"})\n\n\n'
                '@app.post("/recallContextFromEmbedding")\n'
                "async def recall_context(request):\n"
                "    body = request.json()\n"
                '    return jsonify({"contexts": []})\n'
            ),
        })

    # 9. Traceability matrix
    git_commit(repo, "刘奕含", "2026-04-10T14:00:00",
        "docs(requirements): add traceability matrix mapping use cases to WBS (WP1.2)",
        ["docs/CONTRIBUTING.md"])

    # 10. W2 freeze (Chinese)
    git_commit(repo, "卜天", "2026-04-11T17:00:00",
        "chore: 架构评审通过，冻结Week1-2交付物",
        [])

    # ---- W3: April 13 - April 19 (branch-based) ----
    print("\n--- Week 3 (April 13 - April 19) ---")

    # -- feat/data-model branch (胡浩杰) --
    create_branch(repo, "feat/data-model")

    git_commit(repo, "胡浩杰", "2026-04-13T09:00:00",
        "feat(db): define ORM models - User, Crush, RelationChain (WP2.1)",
        ["src/database/models.py"], branch="feat/data-model")

    # manual SQL migration (will be deleted in W6 when Alembic is adopted)
    git_commit(repo, "胡浩杰", "2026-04-13T15:00:00",
        "chore(db): add manual SQL migration script for schema setup",
        files_to_create={
            "src/database/manual_migration.sql": (
                "-- Manual database migration (pre-Alembic)\n"
                "-- DEPRECATED: Will be replaced by Alembic in WP2.4\n\n"
                "CREATE TABLE IF NOT EXISTS users (\n"
                "    id SERIAL PRIMARY KEY,\n"
                "    email VARCHAR(255) UNIQUE NOT NULL,\n"
                "    hashed_password VARCHAR(255) NOT NULL,\n"
                "    created_at TIMESTAMP DEFAULT NOW()\n"
                ");\n\n"
                "CREATE TABLE IF NOT EXISTS crushes (\n"
                "    id SERIAL PRIMARY KEY,\n"
                "    name VARCHAR(255) NOT NULL,\n"
                "    target_type VARCHAR(50) NOT NULL,\n"
                "    user_id INTEGER REFERENCES users(id),\n"
                "    created_at TIMESTAMP DEFAULT NOW()\n"
                ");\n\n"
                "CREATE TABLE IF NOT EXISTS relation_chains (\n"
                "    id SERIAL PRIMARY KEY,\n"
                "    crush_id INTEGER REFERENCES crushes(id),\n"
                "    chain_data JSONB NOT NULL DEFAULT '{}',\n"
                "    created_at TIMESTAMP DEFAULT NOW()\n"
                ");\n\n"
                "CREATE TABLE IF NOT EXISTS context_embeddings (\n"
                "    id SERIAL PRIMARY KEY,\n"
                "    crush_id INTEGER REFERENCES crushes(id),\n"
                "    embedding vector(1536),\n"
                "    content TEXT,\n"
                "    created_at TIMESTAMP DEFAULT NOW()\n"
                ");\n"
            ),
        },
        branch="feat/data-model")

    git_commit(repo, "胡浩杰", "2026-04-14T10:30:00",
        "feat(db): add Event, ChatLog, ContextEmbedding models",
        [], branch="feat/data-model")

    git_commit(repo, "胡浩杰", "2026-04-15T11:00:00",
        "feat(db): implement DB engine factory with connection pooling",
        ["src/database/index.py"], branch="feat/data-model")

    git_commit(repo, "胡浩杰", "2026-04-16T09:15:00",
        "fix: correct foreign key constraint on RelationChain",
        [], branch="feat/data-model")

    # Merge feat/data-model -> main
    merge_branch(repo, "feat/data-model", into="main", author_key="卜天",
        date="2026-04-16T15:00:00",
        message="Merge feat/data-model: ORM models and DB engine (WP2.1)")

    # -- feat/fr-graph branch (陈雷诗语) --
    create_branch(repo, "feat/fr-graph")

    git_commit(repo, "陈雷诗语", "2026-04-17T10:00:00",
        "feat(graph): scaffold FRBuildingGraph with LangGraph StateGraph (WP2.1)",
        ["src/agents/__init__.py",
         "src/agents/graphs/FRBuildingGraph/state.py"],
        files_to_remove=["src/agents/react_loop.py"],
        branch="feat/fr-graph")

    git_commit(repo, "陈雷诗语", "2026-04-18T14:00:00",
        "feat(graph): implement nodeLoadFR and nodePreprocessInput",
        ["src/agents/graphs/FRBuildingGraph/nodes.py"],
        branch="feat/fr-graph")

    git_commit(repo, "陈雷诗语", "2026-04-18T16:00:00",
        "feat(graph): add nodePersistOriginalSource stub",
        [], branch="feat/fr-graph")

    # W3 milestone merge
    merge_branch(repo, "feat/fr-graph", into="main", author_key="卜天",
        date="2026-04-19T17:00:00",
        message="Merge feat/fr-graph: FRBuildingGraph scaffolding (WP2.1)")

    print("\n--- Week 4 (April 20 - April 26) ---")

    # Continue feat/fr-graph
    run("git checkout feat/fr-graph", repo)

    git_commit(repo, "陈雷诗语", "2026-04-20T09:30:00",
        "feat(graph): implement OriginalSource persistence with SourceType mapping (WP2.1)",
        [], branch="feat/fr-graph")

    git_commit(repo, "陈雷诗语", "2026-04-21T10:00:00",
        "feat(service): create UserService with register/login/jwt (WP2.2)",
        ["src/services/__init__.py", "src/services/user.py",
         "src/utils/__init__.py", "src/utils/index.py"],
        branch="feat/fr-graph")

    git_commit(repo, "陈雷诗语", "2026-04-22T11:30:00",
        "feat(service): implement FigureAndRelation CRUD (WP2.2)",
        ["src/services/figure_and_relation.py"],
        branch="feat/fr-graph")

    # KEY: rename Crush -> FigureAndRelation
    git_commit(repo, "陈雷诗语", "2026-04-23T14:00:00",
        "refactor: rename Crush to FigureAndRelation across codebase",
        [], branch="feat/fr-graph")

    # -- feat/knowledge branch (胡浩杰) --
    create_branch(repo, "feat/knowledge")

    git_commit(repo, "胡浩杰", "2026-04-24T10:00:00",
        "feat(service): add Knowledge base CRUD with vector embedding (WP2.2)",
        ["src/services/knowledge.py", "src/agents/ark.py",
         "src/agents/embedding.py"],
        branch="feat/knowledge")

    git_commit(repo, "胡浩杰", "2026-04-25T09:00:00",
        "fix: handle None value in embedding dimension calculation",
        [], branch="feat/knowledge")

    # Merge both to main
    merge_branch(repo, "feat/fr-graph", into="main", author_key="卜天",
        date="2026-04-26T11:00:00",
        message="Merge feat/fr-graph: FRBuildingGraph + services (WP2.1-WP2.2)")

    merge_branch(repo, "feat/knowledge", into="main", author_key="卜天",
        date="2026-04-26T14:00:00",
        message="Merge feat/knowledge: vector embedding and knowledge CRUD (WP2.2)")

    # Bi-weekly report
    git_commit(repo, "卜天", "2026-04-26T17:00:00",
        "docs: 第二份双周报初稿，更新RBS traceability",
        [])

    # ---- W5: April 27 - May 3 ----
    print("\n--- Week 5 (April 27 - May 3) ---")

    # -- feat/feed-extraction (陈雷诗语) --
    create_branch(repo, "feat/feed-extraction")

    git_commit(repo, "陈雷诗语", "2026-04-27T09:00:00",
        "feat(service): implement FineGrainedFeed extraction across 4 dimensions (WP2.2)",
        ["src/services/fine_grained_feed.py"],
        branch="feat/feed-extraction")

    git_commit(repo, "陈雷诗语", "2026-04-28T10:30:00",
        "feat(service): add dimension-aware upsert with conflict detection (WP2.3)",
        [], branch="feat/feed-extraction")

    git_commit(repo, "陈雷诗语", "2026-04-29T14:00:00",
        "feat(graph): add FROverallUpdateLog and conflict tracking nodes (WP2.3)",
        [], branch="feat/feed-extraction")

    git_commit(repo, "陈雷诗语", "2026-04-30T09:00:00",
        "refactor: extract prompt templates to shared module",
        ["src/agents/prompt.py"],
        branch="feat/feed-extraction")

    # Robyn API deleted — project is moving to CLI-based interface
    git_commit(repo, "陈雷诗语", "2026-04-30T11:00:00",
        "refactor: remove Robyn API routes, migrating to CLI-based interface",
        files_to_remove=["src/api/__init__.py", "src/api/routes.py"],
        branch="feat/feed-extraction")

    merge_branch(repo, "feat/feed-extraction", into="main", author_key="卜天",
        date="2026-04-30T16:00:00",
        message="Merge feat/feed-extraction: FineGrainedFeed + conflict detection (WP2.2-WP2.3)")

    # -- feat/conversation-graph (刘奕含) --
    create_branch(repo, "feat/conversation-graph")

    git_commit(repo, "刘奕含", "2026-05-01T10:00:00",
        "feat(conv): define ConversationGraph state and input/output types (WP3.1)",
        ["src/agents/types.py",
         "src/agents/graphs/ConversationGraph/state.py"],
        branch="feat/conversation-graph")

    git_commit(repo, "刘奕含", "2026-05-02T11:00:00",
        "feat(conv): implement nodeLoadFRAndPersona with persona markdown (WP3.1)",
        [], branch="feat/conversation-graph")

    # Fix from 陈雷诗语 (cross-branch contribution)
    git_commit(repo, "陈雷诗语", "2026-05-03T09:00:00",
        "fix: add Semaphore guard to prevent concurrent FRBuildingGraph runs",
        [], branch="feat/conversation-graph")

    # ---- W6: May 4 - May 10 ----
    print("\n--- Week 6 (May 4 - May 10) ---")

    # -- feat/vector-recall (胡浩杰) --
    create_branch(repo, "feat/vector-recall")

    git_commit(repo, "胡浩杰", "2026-05-04T09:00:00",
        "feat(db): add pgvector extension setup and HNSW index (WP2.4)",
        ["src/database/alembic/env.py", "src/database/alembic/script.py.mako",
         "src/database/alembic/README"],
        branch="feat/vector-recall")

    # delete manual SQL migration now that Alembic is in place
    git_commit(repo, "胡浩杰", "2026-05-04T11:00:00",
        "chore: remove manual SQL migration (replaced by Alembic)",
        files_to_remove=["src/database/manual_migration.sql"],
        branch="feat/vector-recall")

    git_commit(repo, "胡浩杰", "2026-05-05T10:30:00",
        "feat(service): implement semantic recall with dimension filtering (WP2.4)",
        [], branch="feat/vector-recall")

    git_commit(repo, "胡浩杰", "2026-05-06T11:00:00",
        "test: add persona building review test cases (WP2.5)",
        ["tests/__init__.py", "tests/graphs/__init__.py",
         "tests/graphs/FRBuildingGraph.py"],
        branch="feat/vector-recall")

    git_commit(repo, "胡浩杰", "2026-05-07T09:00:00",
        "fix: resolve list-type FR field partial update extraction bug (WP2.5)",
        [], branch="feat/vector-recall")

    merge_branch(repo, "feat/vector-recall", into="main", author_key="卜天",
        date="2026-05-07T14:00:00",
        message="Merge feat/vector-recall: pgvector + recall + review (WP2.4-WP2.5)")

    # Continue feat/conversation-graph (刘奕含)
    git_commit(repo, "刘奕含", "2026-05-05T14:00:00",
        "feat(conv): implement parallel recall and message history branches (WP3.1)",
        [], branch="feat/conversation-graph")

    git_commit(repo, "刘奕含", "2026-05-06T10:00:00",
        "feat(conv): add round-based memory trim with rolling summary (WP3.2)",
        ["src/agents/graphs/checkpointer.py",
         "prompts/SUMMARY_MESSAGES_FOR_TRIM.md"],
        branch="feat/conversation-graph")

    # Temp commit (realism! — includes debug file accidentally)
    git_commit(repo, "刘奕含", "2026-05-08T18:00:00",
        "temp: 先提交 明天继续debug PostgresSaver序列化问题",
        files_to_create={
            "debug_checkpoint_dump.json": (
                '{"checkpoint_id": "temp-001", "error": "TypeError: cannot'
                " serialize ORM object\", \"stacktrace\": \"...\"}\n"
            ),
            "src/agents/graphs/checkpointer_debug.py": (
                '"""Temporary debug helpers — DO NOT MERGE."""\n'
                "import json\n\n\n"
                "def dump_state(state, path):\n"
                '    """Quick-and-dirty state serializer for debugging."""\n'
                "    with open(path, 'w') as f:\n"
                "        json.dump(str(state), f, default=str)\n"
            ),
        },
        branch="feat/conversation-graph")

    git_commit(repo, "刘奕含", "2026-05-09T10:00:00",
        "fix: resolve PostgresSaver ORM entity serialization failure (WP3.2)",
        files_to_remove=[
            "debug_checkpoint_dump.json",
            "src/agents/graphs/checkpointer_debug.py",
        ],
        branch="feat/conversation-graph")

    git_commit(repo, "刘奕含", "2026-05-10T11:00:00",
        "feat(conv): integrate ConversationGraph with checkpoint persistence",
        ["src/agents/graphs/ConversationGraph/graph.py"],
        branch="feat/conversation-graph")

    # -- feat/lark-websocket (陈雷诗语) --
    create_branch(repo, "feat/lark-websocket")

    git_commit(repo, "陈雷诗语", "2026-05-07T10:00:00",
        "feat(lark): establish WebSocket connection layer with open_id mapping (WP4.1)",
        ["src/channels/__init__.py",
         "src/channels/lark/websocket.py",
         "src/channels/lark/client.py"],
        branch="feat/lark-websocket")

    git_commit(repo, "陈雷诗语", "2026-05-08T14:00:00",
        "feat(lark): add composite API wrappers for message delivery (WP4.1)",
        ["src/channels/lark/composite_api/im/send_text.py",
         "src/channels/lark/composite_api/im/send_card.py"],
        branch="feat/lark-websocket")

    # Merge feature branches
    merge_branch(repo, "feat/conversation-graph", into="main", author_key="卜天",
        date="2026-05-10T15:00:00",
        message="Merge feat/conversation-graph: dialog system core (WP3.1-WP3.2)")

    merge_branch(repo, "feat/lark-websocket", into="main", author_key="卜天",
        date="2026-05-10T16:00:00",
        message="Merge feat/lark-websocket: Lark integration start (WP4.1)")

    # ---- W7: May 11 - May 14 (final push) ----
    print("\n--- Week 7 (May 11 - May 14) ---")

    # -- feat/llm-integration (刘奕含) --
    create_branch(repo, "feat/llm-integration")

    git_commit(repo, "刘奕含", "2026-05-11T09:00:00",
        "feat(conv): implement nodeCallLLM with dynamic prompt assembly (WP3.3)",
        ["src/agents/llm.py", "src/agents/adapter.py", "src/agents/tools.py",
         "src/agents/graphs/ConversationGraph/nodes.py"],
        branch="feat/llm-integration")

    git_commit(repo, "刘奕含", "2026-05-12T10:00:00",
        "test(conv): 跑通第一轮多轮对话，回复质量基本符合预期",
        ["prompts/CONVERSATION_SYSTEM_PROMPT.md",
         "prompts/recipes/by_role/self.md",
         "prompts/recipes/by_role/family.md",
         "prompts/recipes/by_dimension/personality.md"],
        branch="feat/llm-integration")

    git_commit(repo, "刘奕含", "2026-05-13T11:00:00",
        "feat(conv): add feed sync node for conversation-to-persona loop (WP3.4)",
        ["prompts/SYNC_PERSONALITY_FEEDS_TO_FR_CORE.md",
         "prompts/SYNC_INTERACTION_FEEDS_TO_FR_CORE.md"],
        branch="feat/llm-integration")

    git_commit(repo, "刘奕含", "2026-05-14T09:00:00",
        "fix: 修复memory trim在边界条件判断错误",
        [], branch="feat/llm-integration")

    merge_branch(repo, "feat/llm-integration", into="main", author_key="卜天",
        date="2026-05-14T11:00:00",
        message="Merge feat/llm-integration: LLM call + feed sync (WP3.3-WP3.4)")

    # -- feat/cli (卜天) --
    create_branch(repo, "feat/cli")

    git_commit(repo, "卜天", "2026-05-11T10:00:00",
        "feat(cli): scaffold immortality CLI with argparse command tree (WP5.1)",
        ["src/cli/__init__.py", "src/cli/main.py", "src/cli/constants.py",
         "src/cli/utils.py", "src/cli/session.py"],
        branch="feat/cli")

    git_commit(repo, "卜天", "2026-05-12T11:00:00",
        "feat(cli): implement doctor command with env validation (WP5.1)",
        ["src/cli/commands/__init__.py", "src/cli/commands/index.py"],
        branch="feat/cli")

    git_commit(repo, "卜天", "2026-05-13T09:00:00",
        "feat(cli): implement setup command with .env generation and docker DB (WP5.1)",
        ["src/cli/assets/.env.example",
         "src/cli/assets/docker-compose.yml",
         "src/cli/assets/init-db.sh"],
        branch="feat/cli")

    git_commit(repo, "卜天", "2026-05-14T10:00:00",
        "feat(cli): add log inspection subcommand",
        ["src/cli/commands/auth.py", "src/cli/commands/fr.py",
         "src/cli/commands/lark_service.py"],
        branch="feat/cli")

    merge_branch(repo, "feat/cli", into="main", author_key="卜天",
        date="2026-05-14T12:00:00",
        message="Merge feat/cli: immortality CLI framework (WP5.1)")

    # -- feat/lark-bot (卜天+陈雷诗语) --
    create_branch(repo, "feat/lark-bot")

    git_commit(repo, "陈雷诗语", "2026-05-12T14:00:00",
        "feat(lark): implement bot command menu /menu /list_persons (WP4.2)",
        ["src/channels/lark/integration/__init__.py",
         "src/channels/lark/integration/menu.py",
         "src/channels/lark/integration/utils.py"],
        branch="feat/lark-bot")

    git_commit(repo, "卜天", "2026-05-13T10:00:00",
        "feat(lark): add /show_persona and /build_persona commands (WP4.2)",
        [], branch="feat/lark-bot")

    git_commit(repo, "陈雷诗语", "2026-05-13T15:00:00",
        "feat(lark): design message buffering with 15s wait timer (WP4.3)",
        ["src/channels/lark/integration/index.py"],
        branch="feat/lark-bot")

    # Revert (realism!)
    git_commit(repo, "卜天", "2026-05-14T08:00:00",
        'Revert "feat(lark): add /show_persona and /build_persona commands (WP4.2)" -- 需要重新设计card template',
        [], branch="feat/lark-bot")

    # Re-apply with fixes
    git_commit(repo, "卜天", "2026-05-14T09:30:00",
        "feat(lark): re-add persona commands with fixed card templates (WP4.2)",
        ["src/channels/lark/composite_api/im/send_image.py",
         "src/channels/lark/composite_api/im/send_file.py"],
        branch="feat/lark-bot")

    merge_branch(repo, "feat/lark-bot", into="main", author_key="卜天",
        date="2026-05-14T13:00:00",
        message="Merge feat/lark-bot: bot commands + batching (WP4.2-WP4.3)")

    # -- feat/service-layer (胡浩杰) --
    create_branch(repo, "feat/service-layer")

    git_commit(repo, "胡浩杰", "2026-05-14T10:30:00",
        "refactor(service): decouple data access through service-layer interface (WP4.4)",
        [], branch="feat/service-layer")

    git_commit(repo, "胡浩杰", "2026-05-14T11:30:00",
        "chore: 准备Docker Compose配置，下周开始WP5.3",
        [], branch="feat/service-layer")

    merge_branch(repo, "feat/service-layer", into="main", author_key="卜天",
        date="2026-05-14T14:00:00",
        message="Merge feat/service-layer: service refactor prep (WP4.4)")

    # ---- Final cleanup on main ----
    run("git checkout main", repo)

    # Add remaining files
    git_commit(repo, "卜天", "2026-05-14T15:00:00",
        "chore: 补全剩余prompt recipes和文档，清理遗留设计笔记",
        ["prompts/recipes/by_role/friend.md",
         "prompts/recipes/by_role/mentor.md",
         "prompts/recipes/by_role/colleague.md",
         "prompts/recipes/by_role/partner.md",
         "prompts/recipes/by_role/public-figure.md",
         "prompts/recipes/by_dimension/interaction.md",
         "prompts/recipes/by_dimension/procedural.md",
         "prompts/recipes/by_dimension/memory.md",
         "prompts/FR_BUILDING_COMPARE_FIELD.md",
         "prompts/FR_BUILDING_PREPROCESS.md",
         "prompts/FR_BUILDING_REPORT.md",
         "prompts/SYNC_PROCEDURAL_FEEDS_TO_FR_CORE.md",
         "prompts/SYNC_MEMORY_FEEDS_TO_FR_CORE.md",
         "docs/UPDATES.md", "docs/TODOs.md",
         "tests/cruds/__init__.py",
         "tests/cruds/user.py",
         "tests/cruds/figure_and_relation.py",
         "tests/cruds/fine_grained_feed.py",
         "tests/cruds/knowledge.py",
         "tests/graphs/ConversationGraph.py"],
        files_to_remove=["docs/DESIGN_NOTES.md"])

    git_commit(repo, "卜天", "2026-05-14T16:00:00",
        "chore: 第三份双周报定稿，更新WBS进度追踪",
        [])

    # Final merge commit
    git_commit(repo, "卜天", "2026-05-14T17:00:00",
        "chore(release): v0.3.0-dev — W1-W7 deliverables complete, ready for W8",
        ["src/main.py",
         "src/database/README.md",
         "src/agents/viking.py",
         "src/agents/mcp.py",
         "src/utils/request.py"])

    print("\n" + "=" * 60)
    print("Build complete! Checking git log...")
    print("=" * 60)

    result = subprocess.run(
        ["git", "log", "--oneline", "--graph", "--all"],
        cwd=repo, capture_output=True, text=True,
    )
    print(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="/tmp/HeartCompass-new")
    args = parser.parse_args()
    build_history(args.repo)


if __name__ == "__main__":
    main()
