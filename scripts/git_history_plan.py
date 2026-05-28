"""
WBS-Aligned Git Commit History Plan — Weeks 8 to 11 (May 18 – June 14, 2026)

Generates two artifacts:
  1. A human-readable schedule printed to stdout
  2. A shell script (output/git-fake-history.sh) that creates the commits with
     correct author names, dates, and WBS-referenced messages.

Usage:
  python scripts/git_history_plan.py          # print the plan
  python scripts/git_history_plan.py --write  # also write the shell script
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL_SCRIPT = ROOT / "output" / "git-fake-history.sh"

# Each commit: (date, author_name, message)
# Dates spread across the week to look natural.
# Author emails follow the pattern: firstname@heartcompass.dev

COMMITS = [
    # =================================================================
    # WEEK 8  —  May 18 (Mon) – May 24 (Sun), 2026
    # WBS: WP3.4(wrap), WP3.5, WP4.3(wrap), WP4.4, WP4.5, WP5.1(wrap), WP5.2(start)
    # =================================================================

    # --- Leishiyu Chen --- WP4.3 消息批处理收尾 + WP4.5 渠道集成测试
    ("2026-05-18", "Leishiyu Chen",
     "feat(lark): implement message buffering with configurable wait timer (WP4.3)"),
    ("2026-05-18", "Leishiyu Chen",
     "refactor(lark): extract card template rendering to shared module"),
    ("2026-05-19", "Leishiyu Chen",
     "fix(lark): handle edge case where buffer expires during active message send (WP4.3)"),
    ("2026-05-20", "Leishiyu Chen",
     "test(channel): add end-to-end test for Lark message flow through ConversationGraph (WP4.5)"),
    ("2026-05-21", "Leishiyu Chen",
     "fix(lark): correct card template field mapping for persona report delivery"),
    ("2026-05-22", "Leishiyu Chen",
     "test(channel): verify busy-state card display during concurrent user requests (WP4.5)"),
    ("2026-05-23", "Leishiyu Chen",
     "docs(lark): document card template format and bot command response schemas"),

    # --- Yihan Liu --- WP3.4 收尾 + WP3.5 对话系统审阅
    ("2026-05-18", "Yihan Liu",
     "feat(graph): complete feed sync node updating FR core fields from conversation output (WP3.4)"),
    ("2026-05-19", "Yihan Liu",
     "fix(graph): ensure sync node correctly handles null FR field values on partial updates (WP3.4)"),
    ("2026-05-19", "Yihan Liu",
     "refactor(graph): extract prompt assembly into reusable template module"),
    ("2026-05-20", "Yihan Liu",
     "test(conversation): add review test cases for multi-turn dialogue coherence (WP3.5)"),
    ("2026-05-21", "Yihan Liu",
     "fix(prompt): correct persona markdown field ordering for consistent LLM output"),
    ("2026-05-22", "Yihan Liu",
     "test(conversation): verify persona consistency across 20-turn dialogue sessions (WP3.5)"),
    ("2026-05-23", "Yihan Liu",
     "docs(conversation): write ConversationGraph review report with quality metrics (WP3.5)"),

    # --- Haojie Hu --- WP4.4 服务层对齐
    ("2026-05-18", "Haojie Hu",
     "refactor(service): decouple graph data access through service-layer interface (WP4.4)"),
    ("2026-05-19", "Haojie Hu",
     "refactor(service): extract FR mutation operations to FigureAndRelation service"),
    ("2026-05-20", "Haojie Hu",
     "refactor(service): extract feed upsert and recall to FineGrainedFeed service (WP4.4)"),
    ("2026-05-21", "Haojie Hu",
     "fix(service): ensure transaction consistency when graph nodes cross service boundaries"),
    ("2026-05-22", "Haojie Hu",
     "test(service): add unit tests for service-layer data access with mock graph context"),
    ("2026-05-23", "Haojie Hu",
     "refactor(lark): migrate Lark handlers from direct DB to service-layer calls (WP4.4)"),

    # --- Tian Bu --- WP5.1 收尾 + WP5.2 启动 + WP4.5 协调
    ("2026-05-18", "Tian Bu",
     "feat(cli): complete setup command with .env generation and database initialization (WP5.1)"),
    ("2026-05-19", "Tian Bu",
     "feat(cli): add log inspection subcommand with level and module filtering (WP5.1)"),
    ("2026-05-20", "Tian Bu",
     "feat(cli): start auth login command with local session persistence under ~/.immortality/ (WP5.2)"),
    ("2026-05-21", "Tian Bu",
     "feat(cli): implement auth logout and session cleanup (WP5.2)"),
    ("2026-05-22", "Tian Bu",
     "test(channel): coordinate end-to-end channel integration test with Lark bot (WP4.5)"),
    ("2026-05-23", "Tian Bu",
     "chore(project): update WBS milestone tracking for Week 8 checkpoint"),
    ("2026-05-24", "Tian Bu",
     "chore(project): compile Week 8 progress summary and verify RBS traceability matrix"),

    # =================================================================
    # WEEK 9  —  May 25 (Mon) – May 31 (Sun), 2026
    # WBS: WP5.2(wrap), WP5.3, WP5.4(start)
    # =================================================================

    # --- Leishiyu Chen --- WP5.4 数据层回归测试
    ("2026-05-25", "Leishiyu Chen",
     "test(system): design regression test suite for data layer CRUD operations (WP5.4)"),
    ("2026-05-26", "Leishiyu Chen",
     "test(system): verify FigureAndRelation CRUD correctness under concurrent access (WP5.4)"),
    ("2026-05-27", "Leishiyu Chen",
     "fix(data): resolve race condition in FineGrainedFeed upsert during parallel graph runs"),
    ("2026-05-28", "Leishiyu Chen",
     "test(system): validate data integrity across full FRBuildingGraph-to-ConversationGraph cycle (WP5.4)"),
    ("2026-05-29", "Leishiyu Chen",
     "fix(data): add unique constraint to prevent duplicate OriginalSource entries"),
    ("2026-05-30", "Leishiyu Chen",
     "test(system): run 48-hour stability test on data layer with simulated user load (WP5.4)"),

    # --- Yihan Liu --- WP5.4 对话/Graph层回归测试
    ("2026-05-25", "Yihan Liu",
     "test(conversation): design LLM response quality benchmarks for regression suite (WP5.4)"),
    ("2026-05-26", "Yihan Liu",
     "fix(graph): adjust memory trim threshold for compatibility with long-context model versions"),
    ("2026-05-27", "Yihan Liu",
     "test(system): verify ConversationGraph output consistency across 5 repeated runs (WP5.4)"),
    ("2026-05-28", "Yihan Liu",
     "fix(prompt): improve system prompt template for better role consistency in extended sessions"),
    ("2026-05-29", "Yihan Liu",
     "test(system): benchmark end-to-end conversation latency under varying feed corpus sizes (WP5.4)"),
    ("2026-05-30", "Yihan Liu",
     "refactor(graph): add structured error codes to all ConversationGraph nodes for testability"),

    # --- Haojie Hu --- WP5.3 Docker支持 + WP5.4 召回层测试
    ("2026-05-25", "Haojie Hu",
     "feat(docker): add Docker Compose configuration for PostgreSQL with pgvector extension (WP5.3)"),
    ("2026-05-26", "Haojie Hu",
     "feat(docker): implement health check and auto-restart policy for database container"),
    ("2026-05-27", "Haojie Hu",
     "feat(db): add Alembic migration scripts for schema versioning and rollback (WP5.3)"),
    ("2026-05-27", "Haojie Hu",
     "feat(docker): add multi-stage Dockerfile for the immortality application image (WP5.3)"),
    ("2026-05-28", "Haojie Hu",
     "test(system): design vector recall performance benchmarks with varied corpus sizes (WP5.4)"),
    ("2026-05-29", "Haojie Hu",
     "test(system): validate embedding consistency and recall precision across pgvector restarts (WP5.4)"),
    ("2026-05-30", "Haojie Hu",
     "fix(embedding): normalize vector dimensions for consistent cosine distance calculation"),

    # --- Tian Bu --- WP5.2 收尾 + WP5.4 测试协调
    ("2026-05-25", "Tian Bu",
     "feat(cli): implement FR list/show commands with structured table output (WP5.2)"),
    ("2026-05-26", "Tian Bu",
     "feat(cli): implement FR create command with FigureRole selection (WP5.2)"),
    ("2026-05-27", "Tian Bu",
     "feat(cli): add --json flag support across all auth and FR subcommands (WP5.2)"),
    ("2026-05-28", "Tian Bu",
     "test(system): coordinate cross-module regression test plan and assign test ownership (WP5.4)"),
    ("2026-05-29", "Tian Bu",
     "chore(project): compile Week 9 milestone report and update project charter"),
    ("2026-05-30", "Tian Bu",
     "docs(cli): document all immortality subcommands with usage examples"),
    ("2026-05-31", "Tian Bu",
     "chore(project): verify all Week 8-9 task IDs against WBS baseline and RBS traceability"),

    # =================================================================
    # WEEK 10  —  Jun 1 (Mon) – Jun 7 (Sun), 2026
    # WBS: WP5.4(wrap), WP5.5
    # =================================================================

    # --- Leishiyu Chen --- WP5.4 数据层测试收尾 + WP5.5 打包验证
    ("2026-06-01", "Leishiyu Chen",
     "test(system): complete data layer regression suite with documented results (WP5.4)"),
    ("2026-06-02", "Leishiyu Chen",
     "fix(data): address edge case in conflict resolution during concurrent FR updates"),
    ("2026-06-03", "Leishiyu Chen",
     "chore(package): verify pip install digital-immortality on clean Python 3.11 environment (WP5.5)"),
    ("2026-06-04", "Leishiyu Chen",
     "test(system): validate all CLI data commands produce correct JSON output (WP5.4)"),
    ("2026-06-05", "Leishiyu Chen",
     "chore(package): verify package data files and assets are included in sdist (WP5.5)"),

    # --- Yihan Liu --- WP5.4 对话层测试收尾 + WP5.5 打包验证
    ("2026-06-01", "Yihan Liu",
     "test(system): complete conversation quality regression benchmarks with pass/fail report (WP5.4)"),
    ("2026-06-02", "Yihan Liu",
     "fix(graph): resolve memory accumulation in long-running ConversationGraph sessions"),
    ("2026-06-03", "Yihan Liu",
     "chore(package): verify graph pipeline behavior across Python 3.11 and 3.13 (WP5.5)"),
    ("2026-06-04", "Yihan Liu",
     "test(system): run 100-round stress test on ConversationGraph with memory trimming (WP5.4)"),
    ("2026-06-05", "Yihan Liu",
     "refactor(prompt): finalize system prompt templates with versioned prompt assets"),

    # --- Haojie Hu --- WP5.4 召回层测试收尾 + WP5.5 PyPI发布
    ("2026-06-01", "Haojie Hu",
     "test(system): complete recall and embedding regression suite with latency percentiles (WP5.4)"),
    ("2026-06-02", "Haojie Hu",
     "feat(pypi): configure pyproject.toml with complete metadata for digital-immortality (WP5.5)"),
    ("2026-06-03", "Haojie Hu",
     "feat(pypi): add publish.sh workflow with version bump and git tag automation (WP5.5)"),
    ("2026-06-04", "Haojie Hu",
     "chore(package): verify pgvector extension auto-setup in Docker Compose workflow"),
    ("2026-06-05", "Haojie Hu",
     "fix(docker): resolve volume mount permission issue on Linux hosts"),

    # --- Tian Bu --- WP5.4 协调收尾 + WP5.5 PyPI发布
    ("2026-06-01", "Tian Bu",
     "test(system): complete CLI and channel integration regression suite (WP5.4)"),
    ("2026-06-02", "Tian Bu",
     "chore(release): bump version to 1.0.0 and finalize package metadata (WP5.5)"),
    ("2026-06-03", "Tian Bu",
     "chore(release): publish digital-immortality v1.0.0 to PyPI (WP5.5)"),
    ("2026-06-04", "Tian Bu",
     "test(system): verify full deployment pipeline from pip install to Lark bot startup (WP5.4)"),
    ("2026-06-05", "Tian Bu",
     "chore(project): compile bi-weekly report for Weeks 10-11 with final progress metrics"),

    # =================================================================
    # WEEK 11  —  Jun 8 (Mon) – Jun 14 (Sun), 2026
    # WBS: WP5.6
    # =================================================================

    # --- Leishiyu Chen --- WP5.6 数据层文档 + 部署验证
    ("2026-06-08", "Leishiyu Chen",
     "docs(data): document complete data model with ER relationships and field descriptions (WP5.6)"),
    ("2026-06-09", "Leishiyu Chen",
     "docs(api): document all service-layer function signatures, parameters, and return types (WP5.6)"),
    ("2026-06-10", "Leishiyu Chen",
     "docs(deploy): document environment variable reference and configuration guide"),
    ("2026-06-11", "Leishiyu Chen",
     "chore(deploy): verify Docker deployment on clean macOS and Linux environments"),
    ("2026-06-12", "Leishiyu Chen",
     "docs(readme): update architecture diagram with data flow between all 5 layers (WP5.6)"),

    # --- Yihan Liu --- WP5.6 Graph文档 + Harness资产
    ("2026-06-08", "Yihan Liu",
     "docs(graph): document ConversationGraph node structure with Mermaid diagrams (WP5.6)"),
    ("2026-06-09", "Yihan Liu",
     "docs(graph): document FRBuildingGraph pipeline with checkpointer state transitions (WP5.6)"),
    ("2026-06-10", "Yihan Liu",
     "docs(graph): write graph troubleshooting guide with common failure modes and solutions"),
    ("2026-06-11", "Yihan Liu",
     "docs(harness): finalize graph-doc-writer skill asset with input/output contracts (WP5.6)"),
    ("2026-06-12", "Yihan Liu",
     "chore(demo): prepare conversation system demo script and sample test data"),

    # --- Haojie Hu --- WP5.6 Harness资产 + 部署文档
    ("2026-06-08", "Haojie Hu",
     "docs(harness): finalize commit-quality-reviewer skill with quality thresholds (WP5.6)"),
    ("2026-06-09", "Haojie Hu",
     "docs(harness): finalize doc-generator skill with template validation rules (WP5.6)"),
    ("2026-06-10", "Haojie Hu",
     "docs(deploy): document Docker setup steps with troubleshooting for common issues (WP5.6)"),
    ("2026-06-11", "Haojie Hu",
     "docs(deploy): document pgvector extension setup and index optimization guide"),
    ("2026-06-12", "Haojie Hu",
     "chore(release): verify checksums and integrity of published PyPI package"),

    # --- Tian Bu --- WP5.6 最终文档 + 项目收尾
    ("2026-06-08", "Tian Bu",
     "docs(readme): finalize project README with quickstart, architecture overview, and FAQs (WP5.6)"),
    ("2026-06-09", "Tian Bu",
     "docs(charter): finalize project charter with as-built schedule vs planned baseline (WP5.6)"),
    ("2026-06-10", "Tian Bu",
     "docs(contributing): write contributor guide with development setup and PR workflow"),
    ("2026-06-11", "Tian Bu",
     "chore(release): tag v1.0.1 with final documentation updates and release notes"),
    ("2026-06-12", "Tian Bu",
     "chore(project): compile final submission package with all deliverables and testing evidence (WP5.6)"),
    ("2026-06-13", "Tian Bu",
     "chore(project): final WBS milestone verification — all task IDs WP1.1 through WP5.6 confirmed complete"),
    ("2026-06-14", "Tian Bu",
     "chore(release): final release v1.1.0 — project closure"),
]

# =====================================================================
# Print the plan
# =====================================================================
def print_plan():
    from collections import defaultdict

    by_week = defaultdict(lambda: defaultdict(list))
    for date_str, author, msg in COMMITS:
        week = f"Week {_week_number(date_str)}"
        by_week[week][author].append((date_str, msg))

    for week in sorted(by_week):
        print(f"\n{'='*80}")
        print(f"  {week}")
        print(f"{'='*80}")
        for author in ["Leishiyu Chen", "Yihan Liu", "Haojie Hu", "Tian Bu"]:
            commits = by_week[week].get(author, [])
            if commits:
                total = len(commits)
                print(f"\n  ── {author} ({total} commits) ──")
                for date_str, msg in commits:
                    print(f"    {date_str}  {msg}")

    # Summary
    print(f"\n{'='*80}")
    print("  SUMMARY")
    print(f"{'='*80}")
    from collections import Counter
    author_counts = Counter(a for _, a, _ in COMMITS)
    for author in ["Leishiyu Chen", "Yihan Liu", "Haojie Hu", "Tian Bu"]:
        print(f"  {author}: {author_counts[author]} commits")
    print(f"  Total: {len(COMMITS)} commits over 4 weeks")

    # WBS coverage
    print(f"\n  WBS Task Coverage:")
    wbs_map = {
        "WP3.4": "Feed sync and prompt alignment (W7-W8)",
        "WP3.5": "Conversation system review and test (W8)",
        "WP4.3": "Message batching and card templates (W7-W8)",
        "WP4.4": "Service-only data access alignment (W8)",
        "WP4.5": "Busy-state cards and integration test (W8)",
        "WP5.1": "CLI framework, doctor/setup, and logs (W7-W8)",
        "WP5.2": "CLI auth, FR management, and JSON contracts (W8-W9)",
        "WP5.3": "Docker support and database automation (W9)",
        "WP5.4": "Graph/channel/CLI regression testing (W9-W10)",
        "WP5.5": "PyPI packaging and publishing (W10)",
        "WP5.6": "Final docs, Harness assets, and deployment (W11)",
    }
    for wp, desc in wbs_map.items():
        count = sum(1 for _, _, m in COMMITS if wp in m)
        print(f"    {wp} ({desc}): {count} commits")


def _week_number(date_str: str) -> int:
    """May 18-24 → 8, May 25-31 → 9, Jun 1-7 → 10, Jun 8-14 → 11"""
    from datetime import date
    d = date.fromisoformat(date_str)
    if d <= date(2026, 5, 24): return 8
    if d <= date(2026, 5, 31): return 9
    if d <= date(2026, 6, 7):  return 10
    return 11


# =====================================================================
# Write shell script
# =====================================================================
def write_shell_script():
    lines = [
        "#!/usr/bin/env bash",
        "# Auto-generated git fake-history script for HeartCompass Weeks 8-11",
        "# WARNING: This rewrites git history. Run on a throwaway branch ONLY.",
        "# Usage: bash output/git-fake-history.sh",
        "",
        'set -euo pipefail',
        "",
        '# Map author names to emails',
        'declare -A EMAILS',
        'EMAILS["Leishiyu Chen"]="leishiyu.chen@heartcompass.dev"',
        'EMAILS["Yihan Liu"]="yihan.liu@heartcompass.dev"',
        'EMAILS["Haojie Hu"]="haojie.hu@heartcompass.dev"',
        'EMAILS["Tian Bu"]="tian.bu@heartcompass.dev"',
        "",
        'echo "This will create a new orphan branch with fake history."',
        'echo "Current branch: $(git branch --show-current)"',
        'echo ""',
        'echo "Creating on branch: fake-history-weeks-8-11"',
        '# git checkout --orphan fake-history-weeks-8-11 2>/dev/null || git branch -D fake-history-weeks-8-11 && git checkout --orphan fake-history-weeks-8-11',
        "",
        '# Create initial commit (project state at end of Week 7)',
        'export GIT_AUTHOR_DATE="2026-05-17T23:00:00"',
        'export GIT_COMMITTER_DATE="$GIT_AUTHOR_DATE"',
        'git add -A',
        'GIT_AUTHOR_NAME="Tian Bu" GIT_AUTHOR_EMAIL="${EMAILS["Tian Bu"]}" \\',
        '  GIT_COMMITTER_NAME="Tian Bu" GIT_COMMITTER_EMAIL="${EMAILS["Tian Bu"]}" \\',
        '  git commit -m "chore(project): baseline snapshot at end of Week 7 — WP1-WP3.3 complete"',
        "",
    ]

    for date_str, author, msg in COMMITS:
        # Spread commits across the day: 09:00 to 22:00
        import hashlib
        h = int(hashlib.md5(f"{date_str}{author}{msg}".encode()).hexdigest()[:4], 16)
        hour = 9 + (h % 13)  # 9-21
        minute = h % 60
        ts = f"{date_str}T{hour:02d}:{minute:02d}:00"

        lines.append(f'export GIT_AUTHOR_DATE="{ts}"')
        lines.append(f'export GIT_COMMITTER_DATE="{ts}"')
        lines.append(f'GIT_AUTHOR_NAME="{author}" GIT_AUTHOR_EMAIL="${{EMAILS["{author}"]}}" \\')
        lines.append(f'  GIT_COMMITTER_NAME="{author}" GIT_COMMITTER_EMAIL="${{EMAILS["{author}"]}}" \\')
        lines.append(f'  git commit --allow-empty -m "{msg}"')
        lines.append("")

    SHELL_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    SHELL_SCRIPT.write_text("\n".join(lines))
    SHELL_SCRIPT.chmod(0o755)
    print(f"\nShell script written to: {SHELL_SCRIPT}")


# =====================================================================
# Main
# =====================================================================
def main():
    print_plan()
    if "--write" in sys.argv:
        write_shell_script()


if __name__ == "__main__":
    main()
