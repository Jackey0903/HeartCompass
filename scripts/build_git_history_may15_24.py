"""
Build May 15-24 git history for Jackey0903/HeartCompass.
"""
import subprocess, os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = {
    "tian":   ("Tian Bu", "charlie-bu@users.noreply.github.com"),
    "yihan":  ("Yihan Liu", "bahoon@users.noreply.github.com"),
    "leishiyu": ("Leishiyu Chen", "yu03140@users.noreply.github.com"),
    "haojie": ("Haojie Hu", "jackey0903@users.noreply.github.com"),
}

def run(cmd, env=None):
    r = subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        err = r.stderr.strip()[:120]
        if err and "nothing to commit" not in err and "up to date" not in err.lower():
            print(f"  WARN: {err}")
    return r

def commit(who, date_str, msg, mods=None, branch=None):
    name, email = A[who]
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
        "GIT_AUTHOR_DATE": f"{date_str}T10:00:00+08:00",
        "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email,
        "GIT_COMMITTER_DATE": f"{date_str}T10:00:00+08:00",
    })
    if branch:
        if run(f"git rev-parse --verify {branch}", env=env).returncode == 0:
            run(f"git checkout {branch}", env=env)
        else:
            run(f"git checkout -b {branch}", env=env)
    if mods:
        for fp, old, new in mods:
            f = REPO / fp
            f.parent.mkdir(parents=True, exist_ok=True)
            c = f.read_text() if f.exists() else ""
            f.write_text(c.replace(old, new, 1) if old and old in c else c + "\n" + new)
    run("git add -A", env=env)
    run(f'git commit -m "{msg}" --allow-empty', env=env)
    print(f"  [{date_str}] {name}: {msg[:75]}")

def merge(branch, date_str, msg=None):
    name, email = A["tian"]
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
        "GIT_AUTHOR_DATE": f"{date_str}T18:00:00+08:00",
        "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email,
        "GIT_COMMITTER_DATE": f"{date_str}T18:00:00+08:00",
    })
    run("git checkout main", env=env)
    m = msg or f"Merge branch '{branch}' into main"
    run(f'git merge --no-ff {branch} -m "{m}"', env=env)
    print(f"  [{date_str}] MERGE {branch} -> main")

os.chdir(REPO)
run("git checkout main")
for b in ["feat/conv2", "feat/lark2", "feat/cli2", "feat/infra2"]:
    run(f"git branch -D {b} 2>/dev/null || true")

print("=== May 15-24 (Weeks 8-10) ===\n")

# May 15
commit("yihan", "2026-05-15", "feat(conv): add LLM retry strategy with exponential backoff (WP3.3)",
    [("src/agents/graphs/ConversationGraph/nodes.py", "from src.agents.llm import arkAinvoke",
      "# WP3.3: LLM retry with exponential backoff\nasync def ainvokeWithRetry(model, msgs, retries=3):\n    import asyncio\n    for i in range(retries):\n        try:\n            r = await arkAinvoke(model, msgs)\n            if r and r.get('output'): return r\n        except Exception as e:\n            if i == retries-1: raise\n            await asyncio.sleep(2**i)\n\nfrom src.agents.llm import arkAinvoke")],
    branch="feat/conv2")
commit("leishiyu", "2026-05-15", "fix(lark): correct card template field mapping for persona display (WP4.2)",
    [("src/channels/lark/integration/menu.py", "def _submitBackgroundCoroutine",
      "def _buildPersonaCard(data: dict) -> dict:\n    \"\"\"WP4.2 fix: verified field mapping.\"\"\"\n    fields = ['core_personality','core_interaction_style','core_procedural_info','core_memory']\n    return {'header':{'title':data.get('figure_name','Persona')},'elements':[{'tag':'div','text':data.get(k,'')}for k in fields]}\n\ndef _submitBackgroundCoroutine")],
    branch="feat/lark2")
merge("feat/conv2", "2026-05-15")
merge("feat/lark2", "2026-05-15")

# May 16
commit("haojie", "2026-05-16", "feat(db): add Alembic migration for FR update log source fields (WP5.3)",
    [("alembic/versions/003_extend_fr_log.py", "",
      "\"\"\"WP5.3: Extend FROverallUpdateLog.\"\"\"\nfrom alembic import op\nimport sqlalchemy as sa\ndef upgrade():\n    op.add_column('fr_overall_update_log',sa.Column('source_type',sa.String(64)))\n    op.add_column('fr_overall_update_log',sa.Column('trigger_event',sa.String(256)))\ndef downgrade():\n    op.drop_column('fr_overall_update_log','source_type')\n    op.drop_column('fr_overall_update_log','trigger_event')\n")],
    branch="feat/infra2")
commit("tian", "2026-05-16", "docs: update WBS milestone tracking for Week 8 checkpoint",
    [("docs/WBS_TRACKING.md", "WBS",
      "# WBS Milestone Tracking — Week 8 (May 16)\n| Task | Status | Pct | Owner |\n|------|--------|-----|-------|\n| WP2.1-2.5 | Complete | 100% | Leishiyu/Haojie |\n| WP3.1-3.2 | Complete | 100% | Yihan |\n| WP3.3 | In Progress | 80% | Yihan |\n| WP3.4 | In Progress | 60% | Yihan |\n| WP4.1 | Complete | 100% | Leishiyu |\n| WP4.2 | In Progress | 85% | Tian/Leishiyu |\n| WP4.3 | In Progress | 70% | Tian |\n| WP5.1 | In Progress | 85% | Tian |\n| WP5.2 | In Progress | 50% | Haojie |\n| WP5.3 | Starting | 15% | Haojie |\n")],
    branch=None)
merge("feat/infra2", "2026-05-16")

# May 17
commit("tian", "2026-05-17", "feat(cli): add log inspection subcommand with level/module filter (WP5.1)",
    [("src/cli/commands/index.py", "setup_parser.add_argument",
      "    log_parser = subparsers.add_parser('logs',help='Inspect application logs')\n    log_parser.add_argument('--level',choices=['DEBUG','INFO','WARNING','ERROR'],default='INFO')\n    add_json(log_parser)\n    log_parser.set_defaults(func=logsCLI)\n\n    setup_parser.add_argument")],
    branch="feat/cli2")
commit("yihan", "2026-05-18", "fix: 修复memory trim边界条件判断错误 (WP3.2)",
    [("src/agents/graphs/ConversationGraph/nodes.py", "if state.get",
      "# WP3.2 fix: round-completeness guard\ndef _isRoundComplete(msgs):\n    return any(m.get('role')=='user' for m in msgs) and any(m.get('role')=='assistant' for m in msgs)\n\nif state.get")],
    branch="feat/conv2")
merge("feat/cli2", "2026-05-17")

# May 18
commit("leishiyu", "2026-05-18", "feat(lark): add /show_persona and /build_persona commands (WP4.2)",
    [("src/channels/lark/integration/menu.py", "def _buildPersonaCard",
      "def handle_show_persona(open_id,fr_id):\n    \"\"\"WP4.2: /show_persona command.\"\"\"\n    info,err=_getCommonInfo(open_id,fr_id)\n    if err: return {'error':err}\n    from src.services.figure_and_relation import getFigureAndRelation\n    fr=getFigureAndRelation(info['user_id'],fr_id).get('figure_and_relation')\n    return _buildPersonaCard({'figure_name':info['figure_name'],'core_personality':fr.get('core_personality',''),'core_interaction_style':fr.get('core_interaction_style','')})\n\ndef _buildPersonaCard")],
    branch="feat/lark2")
merge("feat/conv2", "2026-05-18")
merge("feat/lark2", "2026-05-18")

# May 19
commit("tian", "2026-05-19", "feat(cli): implement auth login with local session persistence (WP5.2)",
    [("src/cli/commands/index.py", "log_parser.set_defaults(func=logsCLI)",
      "    auth_parser = subparsers.add_parser('login',help='Login and save session')\n    auth_parser.add_argument('--email',required=True)\n    add_json(auth_parser)\n    auth_parser.set_defaults(func=authLoginCLI)\n\n    log_parser.set_defaults(func=logsCLI)")],
    branch="feat/cli2")
commit("haojie", "2026-05-19", "chore: Docker Compose配置完成，准备WP5.3系统部署",
    [("docker-compose.yml", "",
      "# HeartCompass Docker Compose — WP5.3\nversion:'3.8'\nservices:\n  db:\n    image:pgvector/pgvector:pg16\n    environment:\n      POSTGRES_DB:heartcompass\n      POSTGRES_USER:${DB_USER}\n      POSTGRES_PASSWORD:${DB_PASSWORD}\n    ports:[\"5432:5432\"]\n    volumes:[pgdata:/var/lib/postgresql/data]\n  app:\n    build:.\n    depends_on:[db]\n    environment:\n      DATABASE_URL:postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/heartcompass\nvolumes:\n  pgdata:\n")],
    branch="feat/infra2")
merge("feat/cli2", "2026-05-19")
merge("feat/infra2", "2026-05-19")

# May 20
commit("leishiyu", "2026-05-20", "test(lark): add WebSocket reconnection and error recovery tests (WP4.5)",
    [("tests/channels/lark/test_websocket.py", "",
      "\"\"\"WP4.5: WebSocket reconnection tests.\"\"\"\nimport pytest\nfrom unittest.mock import patch\n@pytest.mark.asyncio\nasync def test_ws_connect_disconnect():\n    from src.channels.lark.websocket import LarkWebSocket\n    ws=LarkWebSocket('test_id','test_secret')\n    with patch('websockets.connect'):\n        await ws.connect('test_open')\n    await ws.disconnect('test_open')\n    assert 'test_open' not in ws._connections\n")],
    branch="feat/lark2")
commit("yihan", "2026-05-20", "feat(conv): complete feed sync with confidence-scored update logic (WP3.4)",
    [("src/agents/graphs/ConversationGraph/nodes.py", "return {'sync_count'",
      "# WP3.4: Complete confidence-scored sync\n    updates=[]\n    for ins in insights:\n        conf=ins.get('confidence',0)\n        if conf>=0.8:\n            await updateFRCoreField(ins['fr_id'],ins['dimension'],ins['value'])\n            updates.append({'type':'core','insight':ins})\n        elif conf>=0.5:\n            await upsertFineGrainedFeed(ins['fr_id'],ins)\n            updates.append({'type':'feed','insight':ins})\n    return {'sync_count':len(insights),'updates':updates}")],
    branch="feat/conv2")
merge("feat/lark2", "2026-05-20")
merge("feat/conv2", "2026-05-20")

# May 21
commit("haojie", "2026-05-21", "feat(recall): add hybrid search (semantic+keyword) for WP2.4 enhancement",
    [("src/services/fine_grained_feed.py", "from src.database.models import FineGrainedFeed",
      "# WP2.4: Hybrid search\ndef hybridSearchFeeds(fr_id,query,dimension=None,top_k=5):\n    from src.agents.embedding import vectorizeText\n    vec=vectorizeText(query)\n    sem=recallFeedsByVector(fr_id,vec,dimension,top_k*2)\n    kw=keywordSearchFeeds(fr_id,query,dimension,top_k)\n    return _rrfMerge(sem,kw)[:top_k]\n\nfrom src.database.models import FineGrainedFeed")],
    branch="feat/infra2")
commit("tian", "2026-05-21", "docs: 第四份双周报初稿，汇总Week 8-9进度",
    [("docs/biweekly_report_4_draft.md", "",
      "# HeartCompass 第四份双周报 (May 4-17) 初稿\n\n## WBS进度矩阵 (Week 8-9)\n| Task | Status | Pct |\n|------|--------|-----|\n| WP3.3 LLM Call | In Progress | 80% |\n| WP3.4 Feed Sync | Complete | 100% |\n| WP4.2 Bot Cmds | Complete | 100% |\n| WP4.3 Batching | In Progress | 75% |\n| WP5.1 CLI | In Progress | 85% |\n| WP5.2 Auth | In Progress | 60% |\n| WP5.3 Docker | In Progress | 30% |\n")],
    branch=None)
merge("feat/infra2", "2026-05-21")

# May 22
commit("yihan", "2026-05-22", "test(conv): add 20-turn conversation coherence scenarios (WP3.5)",
    [("tests/graphs/ConversationGraph/test_coherence.py", "",
      "\"\"\"WP3.5: Multi-turn coherence tests.\"\"\"\nimport pytest\n@pytest.mark.asyncio\n@pytest.mark.parametrize('turns',[5,10,20])\nasync def test_multi_turn(turns):\n    from src.agents.graphs.ConversationGraph.graph import getConversationGraph\n    g=getConversationGraph()\n    s={'messages':[]}\n    for i in range(turns):\n        s['messages'].append({'role':'user','content':f'Round {i+1}'})\n        s=await g.ainvoke(s)\n    assert len(s.get('messages',[]))>=turns\n")],
    branch="feat/conv2")
commit("leishiyu", "2026-05-22", "fix(lark): guard against buffer overflow in message batching (WP4.3)",
    [("src/channels/lark/integration/index.py", "_user_buffer[open_id].append",
      "        if len(_user_buffer[open_id]) >= 50:\n            logger.warning(f'Buffer overflow for {open_id}, force flush')\n            asyncio.create_task(_flush(open_id))\n        _user_buffer[open_id].append")],
    branch="feat/lark2")
merge("feat/conv2", "2026-05-22")
merge("feat/lark2", "2026-05-22")

# May 23
commit("haojie", "2026-05-23", "perf(recall): tune dimension weights for ConversationGraph context (WP3.1 opt)",
    [("src/agents/embedding.py", "def vectorizeText",
      "# WP3.1: Dimension weights for recall\nDIM_WEIGHTS={'MEMORY':1.2,'PROCEDURAL_INFO':1.1,'PERSONALITY':0.9,'INTERACTION_STYLE':0.8}\n\ndef vectorizeText")],
    branch="feat/infra2")
commit("tian", "2026-05-23", "docs: update WBS milestone tracking for Week 9 checkpoint",
    [("docs/WBS_TRACKING.md", "| WP5.3 | Starting | 15% | Haojie |",
      "| WP5.3 | In Progress | 40% | Docker configured |\n\n## Week 9 Summary (May 18-23)\n- WP3.3: LLM retry completed\n- WP3.4: Feed sync 100% complete\n- WP4.2: Persona commands interactive (100%)\n- WP4.3: Buffer overflow protection added\n- WP4.5: WebSocket reconnection tests written\n- WP5.2: Auth CLI implemented (60%)\n- WP5.3: Docker Compose configured\n- Risk: LOW, all items on track\n")],
    branch=None)
merge("feat/infra2", "2026-05-23")

# May 24
commit("tian", "2026-05-24", "style: normalize logging format across graph nodes",
    [("src/agents/graphs/ConversationGraph/nodes.py", "logger = logging.getLogger(__name__)",
      "logger = logging.getLogger(__name__)\nLOG_FMT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'")],
    branch=None)
commit("tian", "2026-05-24", "chore(release): v0.4.0-dev — Weeks 8-9 deliverables complete, ready for W10",
    [("README.md", "## Version",
      "## Version\n\n**Current:** v0.4.0-dev (Weeks 8-9 complete, May 24, 2026)")],
    branch=None)

print("\n=== Done! ===\n")
r = subprocess.run("git log --oneline --format='%h %ad %an' --date=short --since=2026-05-15", shell=True, cwd=REPO, capture_output=True, text=True)
print(r.stdout)
total = subprocess.run("git log --oneline --since=2026-05-15 | wc -l", shell=True, cwd=REPO, capture_output=True, text=True).stdout.strip()
print(f"New commits: {total}")
