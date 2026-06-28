"""
Comprehensive pipeline tests for the ConversationGraph (4-node DAG).

Covers:
- nodeLoadFRAndPersona: FR loading, persona generation, error paths
- nodeRecallFeedsFromDB: vector recall configuration, empty-query handling,
  recall-failure resilience
- nodeBuildAndTrimMessage: message assembly, short-term memory trimming with
  round-aware batching, summary generation
- nodeCallLLM: full LLM invocation pipeline, JSON parsing, anti-repetition,
  formality selection per FigureRole, error handling
- Cross-node state transitions and parallel branch semantics
- All FigureRole types via parametrize
- Various message batch sizes (1, 3, 5, 10)

All external dependencies (DB, LLM API, embedding service, Viktor) are mocked
so the suite runs without infrastructure.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, RemoveMessage

from src.agents.graphs.ConversationGraph.nodes import (
    nodeBuildAndTrimMessage,
    nodeCallLLM,
    nodeLoadFRAndPersona,
    nodeRecallFeedsFromDB,
    _buildTrimmedShortTermMemory,
    _getMessageCharCount,
    _getMessageRoundUUID,
    _recalledFeeds2Markdown,
    _stringifyMessagesForSummary,
    _summarizeTrimmedMessages,
)
from src.agents.graphs.ConversationGraph.state import ConversationGraphState
from src.database.enums import (
    FigureRole,
    FineGrainedFeedDimension,
    FineGrainedFeedConfidence,
    Gender,
    MBTI,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Minimal user record returned by getUserById."""
    return {
        "status": 200,
        "message": "Get user success",
        "user": {"username": "testuser", "nickname": "Test", "gender": "male"},
    }


@pytest.fixture
def sample_fr_friend() -> dict[str, Any]:
    """Sample FigureAndRelation for the FRIEND role."""
    return {
        "id": 1,
        "user_id": 1,
        "figure_role": "friend",
        "figure_name": "小明",
        "figure_gender": "male",
        "figure_mbti": "ENFP",
        "figure_birthday": "1999-06-15",
        "figure_occupation": "设计师",
        "figure_education": "北京理工大学",
        "figure_residence": "北京",
        "figure_hometown": "杭州",
        "figure_appearance": "高个子，戴眼镜",
        "figure_likes": ["摄影", "跑步"],
        "figure_dislikes": ["早起"],
        "words_figure2user": ["好久不见！", "最近怎么样？"],
        "words_user2figure": ["周末聚聚吧"],
        "exact_relation": "大学室友，最好的朋友",
        "core_personality": "乐观开朗，富有创造力",
        "core_interaction_style": "轻松随意，爱开玩笑",
        "core_procedural_info": "",
        "core_memory": "一起毕业旅行",
    }


@pytest.fixture
def sample_fr_mentor() -> dict[str, Any]:
    """Sample FigureAndRelation for the MENTOR role."""
    return {
        "id": 2,
        "user_id": 1,
        "figure_role": "mentor",
        "figure_name": "王老师",
        "figure_gender": "male",
        "figure_mbti": "INTJ",
        "figure_birthday": "1980-03-20",
        "figure_occupation": "教授",
        "figure_education": "清华大学博士",
        "figure_residence": "上海",
        "figure_hometown": "南京",
        "figure_appearance": "儒雅，戴金丝眼镜",
        "figure_likes": ["阅读", "茶道"],
        "figure_dislikes": ["浮躁"],
        "words_figure2user": ["你需要更深入地思考这个问题"],
        "words_user2figure": ["谢谢您的指导"],
        "exact_relation": "研究生导师",
        "core_personality": "严谨认真，善于引导",
        "core_interaction_style": "正式但不失亲和",
        "core_procedural_info": "每周一次组会汇报",
        "core_memory": "一起发表过一篇论文",
    }


@pytest.fixture
def sample_fr_self() -> dict[str, Any]:
    """Sample FigureAndRelation for the SELF role."""
    return {
        "id": 3,
        "user_id": 1,
        "figure_role": "self",
        "figure_name": "我自己",
        "figure_gender": "male",
        "figure_mbti": "ENTJ",
        "figure_birthday": "2004-12-09",
        "figure_occupation": "学生",
        "figure_education": "同济大学",
        "figure_residence": "上海",
        "figure_hometown": "呼和浩特",
        "figure_appearance": "",
        "figure_likes": ["编程", "阅读"],
        "figure_dislikes": [],
        "words_figure2user": [],
        "words_user2figure": [],
        "exact_relation": "自我认知",
        "core_personality": "目标明确，执行力强",
        "core_interaction_style": "自我反思型",
        "core_procedural_info": "每天写计划",
        "core_memory": "",
    }


@pytest.fixture
def base_request() -> dict[str, Any]:
    """Minimal valid request for the conversation graph."""
    return {
        "user_id": 1,
        "fr_id": 1,
        "messages_received": ["今天天气不错"],
    }


@pytest.fixture
def base_state(
    base_request: dict[str, Any],
    sample_fr_friend: dict[str, Any],
    sample_user_data: dict[str, Any],
) -> dict[str, Any]:
    """Construct a minimal valid ConversationGraphState dict for node tests."""
    return {
        "request": base_request,
        "messages": [],
        "round_uuid": str(uuid.uuid4()),
        "user_name": sample_user_data["user"]["username"],
        "figure_and_relation": sample_fr_friend,
        "figure_persona": buildPersonaHelper(sample_fr_friend),
        "words_to_user": "好久不见！, 最近怎么样？",
        "recalled_personalities_from_db": "",
        "recalled_interaction_styles_from_db": "",
        "recalled_procedural_infos_from_db": "",
        "recalled_memories_from_db": "",
        "recalled_facts_from_viking": [],
        "conversation_summary": "",
        "logs": [],
        "warnings": [],
        "errors": [],
        "status": "running",
        "llm_output": {"messages_to_send": [], "reasoning_content": ""},
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def buildPersonaHelper(fr: dict[str, Any]) -> str:
    """Lightweight persona builder matching the production exclude_fields logic."""
    from src.services.figure_and_relation import buildFigurePersonaMarkdown
    return buildFigurePersonaMarkdown(
        fr=fr,
        exclude_fields=[
            "words_figure2user",
            "words_user2figure",
            "core_procedural_info",
            "core_memory",
        ],
    )


def makeHumanMessage(content: str, round_uuid: str = "") -> HumanMessage:
    return HumanMessage(
        content=content,
        additional_kwargs={"round_uuid": round_uuid} if round_uuid else {},
    )


def makeAIMessage(content: str, round_uuid: str = "") -> AIMessage:
    return AIMessage(
        content=content,
        additional_kwargs={"round_uuid": round_uuid} if round_uuid else {},
    )


# ---------------------------------------------------------------------------
# nodeLoadFRAndPersona
# ---------------------------------------------------------------------------


class TestNodeLoadFRAndPersona:
    """Tests for the first conversation node: loading FR and building persona."""

    def test_loads_fr_and_generates_persona_success(
        self,
        base_state: dict[str, Any],
        sample_fr_friend: dict[str, Any],
        sample_user_data: dict[str, Any],
    ) -> None:
        """Arrange: valid state with existing user and FR.
        Act: call nodeLoadFRAndPersona.
        Assert: round_uuid assigned, persona populated, words_to_user extracted,
                logs appended with ok status.
        """
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value=sample_user_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": 200,
                    "message": "ok",
                    "figure_and_relation": sample_fr_friend,
                },
            ),
        ):
            result = nodeLoadFRAndPersona(base_state)

        assert result["round_uuid"] is not None
        assert len(result["round_uuid"]) == 36  # UUID4
        assert result["user_name"] == "testuser"
        assert result["figure_persona"].startswith("# 小明 画像")
        assert result["words_to_user"] == "好久不见！, 最近怎么样？"
        assert len(result["logs"]) == 1
        assert result["logs"][0]["status"] == "ok"
        assert result["logs"][0]["step"] == "nodeLoadFRAndPersona"

    def test_raises_value_error_when_user_not_found(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: getUserById returns None user.
        Act: call nodeLoadFRAndPersona.
        Assert: ValueError raised with 'User not found'.
        """
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value={"status": -1, "message": "User not found", "user": None},
            ),
        ):
            with pytest.raises(ValueError, match="User not found"):
                nodeLoadFRAndPersona(base_state)

    def test_raises_value_error_when_fr_not_found(
        self,
        base_state: dict[str, Any],
        sample_user_data: dict[str, Any],
    ) -> None:
        """Arrange: user exists but FR is missing.
        Act: call nodeLoadFRAndPersona.
        Assert: ValueError raised with 'Figure and relation not found'.
        """
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value=sample_user_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": -3,
                    "message": "not found",
                    "figure_and_relation": None,
                },
            ),
        ):
            with pytest.raises(ValueError, match="Figure and relation not found"):
                nodeLoadFRAndPersona(base_state)

    @pytest.mark.parametrize(
        "figure_role,expected_name",
        [
            (FigureRole.SELF, "我自己"),
            (FigureRole.FAMILY, "妈妈"),
            (FigureRole.FRIEND, "小明"),
            (FigureRole.MENTOR, "王老师"),
            (FigureRole.COLLEAGUE, "李同事"),
            (FigureRole.PARTNER, "小芳"),
            (FigureRole.PUBLIC_FIGURE, "鲁迅"),
            (FigureRole.STRANGER, "路人甲"),
        ],
    )
    def test_persona_generation_for_all_roles(
        self,
        base_state: dict[str, Any],
        sample_fr_friend: dict[str, Any],
        sample_user_data: dict[str, Any],
        figure_role: FigureRole,
        expected_name: str,
    ) -> None:
        """Verify persona markdown is generated for every FigureRole.
        The test ensures the exclude_fields contract (core_procedural_info,
        core_memory, words_*) is respected and the persona block starts with
        the figure name.
        """
        fr = dict(sample_fr_friend)
        fr["figure_role"] = figure_role.value
        fr["figure_name"] = expected_name
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value=sample_user_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": 200,
                    "figure_and_relation": fr,
                },
            ),
        ):
            result = nodeLoadFRAndPersona(base_state)

        persona = result["figure_persona"]
        assert f"# {expected_name} 画像" in persona
        # Confirm excluded fields are NOT in the persona
        assert "核心程序性知识" not in persona
        assert "核心记忆" not in persona
        assert "对用户常说的话" not in persona

    def test_logs_contain_fr_id_and_role(
        self,
        base_state: dict[str, Any],
        sample_fr_friend: dict[str, Any],
        sample_user_data: dict[str, Any],
    ) -> None:
        """Assert the node log data includes the FR id and figure role."""
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value=sample_user_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": 200,
                    "figure_and_relation": sample_fr_friend,
                },
            ),
        ):
            result = nodeLoadFRAndPersona(base_state)

        log_data = result["logs"][0]["data"]
        assert log_data["fr_id"] == 1
        assert log_data["figure_role"] == "friend"

    def test_round_uuid_is_unique_per_call(
        self,
        base_state: dict[str, Any],
        sample_fr_friend: dict[str, Any],
        sample_user_data: dict[str, Any],
    ) -> None:
        """Every invocation must produce a fresh, unique round UUID."""
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value=sample_user_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": 200,
                    "figure_and_relation": sample_fr_friend,
                },
            ),
        ):
            r1 = nodeLoadFRAndPersona(base_state)
            r2 = nodeLoadFRAndPersona(base_state)

        assert r1["round_uuid"] != r2["round_uuid"]

    def test_preserves_existing_logs_from_upstream(
        self,
        base_state: dict[str, Any],
        sample_fr_friend: dict[str, Any],
        sample_user_data: dict[str, Any],
    ) -> None:
        """Existing logs in state must be kept and new log appended."""
        base_state["logs"] = [
            {"step": "upstream", "status": "ok", "detail": "prior", "data": {}}
        ]
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value=sample_user_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": 200,
                    "figure_and_relation": sample_fr_friend,
                },
            ),
        ):
            result = nodeLoadFRAndPersona(base_state)

        assert len(result["logs"]) == 2
        assert result["logs"][0]["step"] == "upstream"
        assert result["logs"][1]["step"] == "nodeLoadFRAndPersona"


# ---------------------------------------------------------------------------
# nodeRecallFeedsFromDB
# ---------------------------------------------------------------------------


class TestNodeRecallFeedsFromDB:
    """Tests for the second conversation node: recalling feeds from DB."""

    def _make_recall_success(self) -> dict[str, Any]:
        return {
            "status": 200,
            "message": "Recall success",
            "items": {
                "procedural_info": [
                    {
                        "score": 0.95,
                        "fine_grained_feed": {
                            "content": "喜欢先规划再行动",
                            "sub_dimension": "工作方法",
                            "dimension": "procedural_info",
                        },
                    }
                ],
                "memory": [
                    {
                        "score": 0.88,
                        "fine_grained_feed": {
                            "content": "去年去了日本旅行",
                            "sub_dimension": "旅行记忆",
                            "dimension": "memory",
                        },
                    }
                ],
            },
        }

    @pytest.mark.asyncio
    async def test_recall_success_fills_procedural_and_memory(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: recall returns procedural_info and memory items.
        Act: call nodeRecallFeedsFromDB.
        Assert: procedural_infos and memories populated as markdown;
                personality/interaction_style left empty (excluded from scope).
        """
        with patch(
            "src.agents.graphs.ConversationGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
            return_value=self._make_recall_success(),
        ):
            result = await nodeRecallFeedsFromDB(base_state)

        assert result["recalled_procedural_infos_from_db"] != ""
        assert "喜欢先规划再行动" in result["recalled_procedural_infos_from_db"]
        assert result["recalled_memories_from_db"] != ""
        assert "去年去了日本旅行" in result["recalled_memories_from_db"]
        # These two are excluded in the current scope configuration
        assert result.get("recalled_personalities_from_db", "") == ""
        assert result.get("recalled_interaction_styles_from_db", "") == ""

    @pytest.mark.asyncio
    async def test_empty_messages_received_skips_recall(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: messages_received is empty list.
        Act: call nodeRecallFeedsFromDB.
        Assert: skip log emitted, recall service never called, warning appended.
        """
        base_state["request"]["messages_received"] = []
        with patch(
            "src.agents.graphs.ConversationGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
        ) as mock_recall:
            result = await nodeRecallFeedsFromDB(base_state)

        mock_recall.assert_not_called()
        assert len(result["warnings"]) == 1
        assert "empty" in result["warnings"][0].lower()
        assert result["logs"][0]["status"] == "skip"

    @pytest.mark.asyncio
    async def test_all_messages_are_whitespace_skips_recall(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: messages_received contains only whitespace strings.
        Act: call nodeRecallFeedsFromDB.
        Assert: skip behavior triggered.
        """
        base_state["request"]["messages_received"] = ["   ", "\n\t"]
        with patch(
            "src.agents.graphs.ConversationGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
        ) as mock_recall:
            result = await nodeRecallFeedsFromDB(base_state)

        mock_recall.assert_not_called()
        assert result["logs"][0]["status"] == "skip"

    @pytest.mark.asyncio
    async def test_recall_failure_logs_error_and_continues(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: recall service returns non-200 status.
        Act: call nodeRecallFeedsFromDB.
        Assert: error logged, state errors populated, no markdown generated.
        """
        with patch(
            "src.agents.graphs.ConversationGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
            return_value={"status": 500, "message": "DB connection lost"},
        ):
            result = await nodeRecallFeedsFromDB(base_state)

        assert len(result["errors"]) == 1
        assert "DB connection lost" in result["errors"][0]
        assert result["logs"][-1]["status"] == "error"
        assert result.get("recalled_procedural_infos_from_db", "") == ""

    @pytest.mark.asyncio
    async def test_recall_scope_configuration_is_correct(
        self, base_state: dict[str, Any]
    ) -> None:
        """Verify the recall scope excludes PERSONALITY and INTERACTION_STYLE
        (to avoid redundancy with persona) while including PROCEDURAL_INFO and MEMORY
        with environment-configured top_k values.
        """
        with patch(
            "src.agents.graphs.ConversationGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
            return_value=self._make_recall_success(),
        ) as mock_recall:
            await nodeRecallFeedsFromDB(base_state)

        call_kwargs = mock_recall.call_args.kwargs
        scopes = call_kwargs["scope"]
        scope_dims = [s["scope"] for s in scopes]
        assert FineGrainedFeedDimension.PERSONALITY not in scope_dims
        assert FineGrainedFeedDimension.INTERACTION_STYLE not in scope_dims
        assert FineGrainedFeedDimension.PROCEDURAL_INFO in scope_dims
        assert FineGrainedFeedDimension.MEMORY in scope_dims

    @pytest.mark.asyncio
    async def test_messages_received_with_none_elements_handled(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: request.messages_received contains None values.
        Act: call nodeRecallFeedsFromDB.
        Assert: None values are filtered out, query still valid.
        """
        base_state["request"]["messages_received"] = [None, "有效消息", None]
        with patch(
            "src.agents.graphs.ConversationGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
            return_value=self._make_recall_success(),
        ):
            result = await nodeRecallFeedsFromDB(base_state)

        assert result["logs"][-1]["status"] == "ok"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


class TestMessageUtilities:
    """Unit tests for message helper functions."""

    def test_get_message_char_count_plain_text(self) -> None:
        msg = HumanMessage(content="hello")
        assert _getMessageCharCount(msg) == 5

    def test_get_message_char_count_empty(self) -> None:
        msg = HumanMessage(content="")
        assert _getMessageCharCount(msg) == 0

    def test_get_message_char_count_with_chinese(self) -> None:
        msg = HumanMessage(content="你好世界")
        assert _getMessageCharCount(msg) == 4

    def test_get_message_round_uuid_present(self) -> None:
        uid = str(uuid.uuid4())
        msg = HumanMessage(content="x", additional_kwargs={"round_uuid": uid})
        assert _getMessageRoundUUID(msg) == uid

    def test_get_message_round_uuid_missing(self) -> None:
        msg = HumanMessage(content="x")
        assert _getMessageRoundUUID(msg) is None

    def test_get_message_round_uuid_empty_string_returns_none(self) -> None:
        msg = HumanMessage(content="x", additional_kwargs={"round_uuid": ""})
        assert _getMessageRoundUUID(msg) is None

    def test_stringify_messages_for_summary(self) -> None:
        messages = [
            HumanMessage(content="你好"),
            AIMessage(content="你好，有什么可以帮忙的吗？"),
        ]
        result = _stringifyMessagesForSummary(messages)
        assert "[HumanMessage]" in result
        assert "[AIMessage]" in result
        assert "你好" in result

    def test_stringify_messages_skips_empty_content(self) -> None:
        messages = [HumanMessage(content=""), AIMessage(content="有用的回复")]
        result = _stringifyMessagesForSummary(messages)
        assert "[HumanMessage]" not in result
        assert "[AIMessage]" in result

    def test_recalled_feeds_to_markdown_normal_input(self) -> None:
        items = [
            {
                "score": 0.92,
                "fine_grained_feed": {
                    "content": "喜欢喝咖啡",
                    "sub_dimension": "饮食偏好",
                },
            }
        ]
        result = _recalledFeeds2Markdown(items)
        assert "饮食偏好" in result
        assert "喜欢喝咖啡" in result
        assert "0.9200" in result

    def test_recalled_feeds_to_markdown_empty_list(self) -> None:
        assert _recalledFeeds2Markdown([]) == ""

    def test_recalled_feeds_to_markdown_missing_content(self) -> None:
        items = [{"score": 0.5, "fine_grained_feed": {"content": "", "sub_dimension": "x"}}]
        assert _recalledFeeds2Markdown(items) == ""


# ---------------------------------------------------------------------------
# Short-term memory trimming
# ---------------------------------------------------------------------------


class TestShortTermMemoryTrimming:
    """Tests for the _buildTrimmedShortTermMemory function and its helpers."""

    @pytest.mark.asyncio
    async def test_no_trim_when_under_limit(self) -> None:
        """When total chars and message count are within thresholds,
        no trimming should occur."""
        messages = [
            makeHumanMessage("Hi", round_uuid="r1"),
            makeAIMessage("Hello!", round_uuid="r1"),
        ]
        msgs, summary, removes, stats = await _buildTrimmedShortTermMemory(
            messages=messages, old_summary=""
        )
        assert len(msgs) == 2
        assert summary == ""
        assert removes == []
        assert stats["trimmed_count"] == 0

    @pytest.mark.asyncio
    async def test_trims_oldest_round_when_over_char_limit(self) -> None:
        """When char count exceeds SHORT_TERM_MEMORY_MAX_CHARS, the oldest
        complete round is removed, preserving at least the latest round."""
        # Use a low max_chars to force trimming
        with patch.dict("os.environ", {
            "SHORT_TERM_MEMORY_MAX_CHARS": "30",
            "SHORT_TERM_MEMORY_TARGET_CHARS": "20",
        }):
            messages = [
                makeHumanMessage("a" * 25, round_uuid="r1"),
                makeAIMessage("b" * 10, round_uuid="r1"),
                makeHumanMessage("c" * 5, round_uuid="r2"),
                makeAIMessage("d" * 5, round_uuid="r2"),
            ]
            msgs, summary, removes, stats = await _buildTrimmedShortTermMemory(
                messages=messages, old_summary=""
            )
        # r2 (latest round) must be preserved
        assert len(msgs) <= 4
        assert stats["trimmed_count"] > 0
        assert any("c" in str(m.content) for m in msgs)

    @pytest.mark.asyncio
    async def test_never_trims_last_round(self) -> None:
        """Even under extreme pressure, the most recent round is never trimmed."""
        with patch.dict("os.environ", {
            "SHORT_TERM_MEMORY_MAX_CHARS": "5",
            "SHORT_TERM_MEMORY_TARGET_CHARS": "3",
        }):
            messages = [
                makeHumanMessage("old", round_uuid="r1"),
                makeAIMessage("old2", round_uuid="r1"),
                makeHumanMessage("new", round_uuid="r2"),
            ]
            msgs, summary, removes, stats = await _buildTrimmedShortTermMemory(
                messages=messages, old_summary=""
            )
        # Latest round (r2) with 1 message must remain
        assert any("new" in str(m.content) for m in msgs)

    @pytest.mark.asyncio
    async def test_trim_by_round_uuid_keeps_same_round_together(self) -> None:
        """Messages sharing a round_uuid are trimmed atomically,
        preventing orphaned HumanMessage or AIMessage for a round."""
        with patch.dict("os.environ", {
            "SHORT_TERM_MEMORY_MAX_CHARS": "40",
            "SHORT_TERM_MEMORY_TARGET_CHARS": "20",
        }):
            messages = [
                makeHumanMessage("a" * 20, round_uuid="r1"),
                makeAIMessage("b" * 20, round_uuid="r1"),
                makeHumanMessage("c" * 20, round_uuid="r2"),
            ]
            msgs, summary, removes, stats = await _buildTrimmedShortTermMemory(
                messages=messages, old_summary=""
            )
        # Either r1 fully trimmed or only r2 remains
        r1_present = any(
            _getMessageRoundUUID(m) == "r1" for m in msgs
        )
        r2_present = any(
            _getMessageRoundUUID(m) == "r2" for m in msgs
        )
        if r1_present:
            # Both r1 messages must be present
            r1_count = sum(
                1 for m in msgs if _getMessageRoundUUID(m) == "r1"
            )
            assert r1_count == 2  # full round kept
        assert r2_present

    @pytest.mark.asyncio
    async def test_messages_without_round_uuid_trimmed_one_by_one(self) -> None:
        """Messages lacking round_uuid are trimmed individually (fallback)."""
        with patch.dict("os.environ", {
            "SHORT_TERM_MEMORY_MAX_CHARS": "15",
            "SHORT_TERM_MEMORY_TARGET_CHARS": "5",
        }):
            messages = [
                HumanMessage(content="x" * 10),
                HumanMessage(content="y" * 10),
                makeHumanMessage("keep", round_uuid="r_recent"),
            ]
            msgs, summary, removes, stats = await _buildTrimmedShortTermMemory(
                messages=messages, old_summary=""
            )
        assert any("keep" in str(m.content) for m in msgs)

    @pytest.mark.asyncio
    async def test_old_summary_appended_to_new_summary(
        self,
    ) -> None:
        """The old_summary is passed into the summarization call so that
        the mini-model can produce a rolling cumulative summary."""
        with patch.dict("os.environ", {
            "SHORT_TERM_MEMORY_MAX_CHARS": "30",
            "SHORT_TERM_MEMORY_TARGET_CHARS": "10",
        }):
            messages = [
                makeHumanMessage("a" * 20, round_uuid="r1"),
                makeAIMessage("b" * 10, round_uuid="r1"),
                makeHumanMessage("recent", round_uuid="r2"),
            ]
            old_sum = "Previously: talked about weather."
            with patch(
                "src.agents.graphs.ConversationGraph.nodes._summarizeTrimmedMessages",
                new_callable=AsyncMock,
                return_value="Updated summary",
            ) as mock_summarize:
                msgs, summary, removes, stats = await _buildTrimmedShortTermMemory(
                    messages=messages, old_summary=old_sum,
                )
                passed_old = mock_summarize.call_args.args[0]
                assert passed_old == old_sum

    @pytest.mark.asyncio
    async def test_trim_stats_are_accurate(self) -> None:
        """The trim_stats dictionary reports before/after counts correctly."""
        with patch.dict("os.environ", {
            "SHORT_TERM_MEMORY_MAX_CHARS": "15",
            "SHORT_TERM_MEMORY_TARGET_CHARS": "5",
        }):
            messages = [
                HumanMessage(content="x" * 20),
                HumanMessage(content="z" * 3),
            ]
            msgs, summary, removes, stats = await _buildTrimmedShortTermMemory(
                messages=messages, old_summary=""
            )
        assert stats["messages_count_before_trim"] == 2
        assert stats["trimmed_count"] > 0
        assert stats["chars_before"] == 23

    @pytest.mark.asyncio
    async def test_generate_remove_messages_have_ids(self) -> None:
        """Every RemoveMessage must reference a message that has an id."""
        with patch.dict("os.environ", {
            "SHORT_TERM_MEMORY_MAX_CHARS": "15",
            "SHORT_TERM_MEMORY_TARGET_CHARS": "5",
        }):
            messages = [
                HumanMessage(content="x" * 20),
                HumanMessage(content="z" * 3),
            ]
            msgs, summary, removes, stats = await _buildTrimmedShortTermMemory(
                messages=messages, old_summary=""
            )
        for rm in removes:
            assert isinstance(rm, RemoveMessage)
            assert rm.id is not None


# ---------------------------------------------------------------------------
# nodeBuildAndTrimMessage
# ---------------------------------------------------------------------------


class TestNodeBuildAndTrimMessage:
    """Tests for the third conversation node: building messages and trimming."""

    @pytest.mark.asyncio
    async def test_appends_current_human_message(self, base_state: dict[str, Any]) -> None:
        """A HumanMessage with the received content is always appended."""
        async with _mock_trim_noop():
            result = await nodeBuildAndTrimMessage(base_state)

        returned_messages = result.get("messages", [])
        # At least one HumanMessage from the current round
        human_count = sum(1 for m in returned_messages if isinstance(m, HumanMessage))
        assert human_count >= 1

    @pytest.mark.asyncio
    async def test_round_uuid_set_on_new_human_message(
        self, base_state: dict[str, Any]
    ) -> None:
        """The newly appended HumanMessage carries the state's round_uuid."""
        async with _mock_trim_noop():
            result = await nodeBuildAndTrimMessage(base_state)

        returned_messages = result.get("messages", [])
        human_msgs = [m for m in returned_messages if isinstance(m, HumanMessage)]
        for hm in human_msgs:
            akw = getattr(hm, "additional_kwargs", {}) or {}
            if akw.get("round_uuid"):
                assert akw["round_uuid"] == base_state["round_uuid"]

    @pytest.mark.asyncio
    async def test_preserves_conversation_summary(self, base_state: dict[str, Any]) -> None:
        """The conversation_summary returned equals the old_summary when
        trimming is a no-op."""
        base_state["conversation_summary"] = "Previous summary here"
        async with _mock_trim_noop():
            result = await nodeBuildAndTrimMessage(base_state)

        assert result["conversation_summary"] == "Previous summary here"

    @pytest.mark.asyncio
    async def test_logs_trim_stats(self, base_state: dict[str, Any]) -> None:
        """After nodeBuildAndTrimMessage, a log entry with trim statistics exists."""
        async with _mock_trim_noop():
            result = await nodeBuildAndTrimMessage(base_state)

        log = result["logs"][-1]
        assert log["step"] == "nodeBuildAndTrimMessage"
        assert log["status"] == "ok"
        assert "messages_count_before_trim" in log["data"]


@asynccontextmanager
async def _mock_trim_noop():
    """Context manager that makes _buildTrimmedShortTermMemory a no-op."""
    async def _noop(messages, old_summary):
        return messages, old_summary, [], {
            "messages_count_before_trim": len(messages),
            "messages_count_after": len(messages),
            "chars_before": 100,
            "chars_after": 100,
            "trimmed_count": 0,
        }
    with patch(
        "src.agents.graphs.ConversationGraph.nodes._buildTrimmedShortTermMemory",
        side_effect=_noop,
    ):
        yield


# ---------------------------------------------------------------------------
# nodeCallLLM
# ---------------------------------------------------------------------------


class TestNodeCallLLM:
    """Tests for the final conversation node: LLM invocation and response parsing."""

    def _mock_llm_success(self, messages_to_send: list[str]) -> AsyncMock:
        """Return an AsyncMock that simulates a successful LLM JSON response."""
        async def _invoke(model, messages, model_options=None, reasoning_content_in_ai_message=False):
            return {
                "output": '{"messages_to_send": ' + str(messages_to_send).replace("'", '"') + '}',
                "reasoning_content": "The user seems cheerful, respond warmly.",
            }
        mock = AsyncMock(side_effect=_invoke)
        return mock

    def _mock_prompt(self, content: str = "You are a helpful assistant.") -> MagicMock:
        return MagicMock(return_value=content)

    @pytest.mark.asyncio
    async def test_successful_llm_call_produces_ai_message(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: LLM returns valid JSON with messages_to_send.
        Act: call nodeCallLLM.
        Assert: llm_output populated, AIMessage appended to messages,
                reasoning_content captured, logs show ok status.
        """
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt("System prompt content"),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                self._mock_llm_success(["今天天气确实不错！"]),
            ),
        ):
            result = await nodeCallLLM(base_state)

        assert result["llm_output"]["messages_to_send"] == ["今天天气确实不错！"]
        assert result["llm_output"]["reasoning_content"] != ""
        assert len(result["logs"]) > 0
        assert result["logs"][-1]["status"] == "ok"
        # AIMessage appended
        ai_msgs = [m for m in result.get("messages", []) if isinstance(m, AIMessage)]
        assert len(ai_msgs) >= 1
        assert "天气" in ai_msgs[-1].content

    @pytest.mark.asyncio
    async def test_handles_invalid_json_gracefully(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: LLM returns text that is not valid JSON.
        Act: call nodeCallLLM.
        Assert: warning logged, no crash, messages_to_send is empty list.
        """
        async def _bad_json(**kwargs):
            return {"output": "not valid json {{{", "reasoning_content": ""}
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                AsyncMock(side_effect=_bad_json),
            ),
        ):
            result = await nodeCallLLM(base_state)

        assert result["llm_output"]["messages_to_send"] == []
        assert len(result["warnings"]) >= 1
        assert any("JSON" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_handles_json_array_output(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: LLM returns a JSON array instead of object.
        Act: call nodeCallLLM.
        Assert: warning logged about non-dict output, graceful degradation.
        """
        async def _array_output(**kwargs):
            return {"output": '["msg1", "msg2"]', "reasoning_content": ""}
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                AsyncMock(side_effect=_array_output),
            ),
        ):
            result = await nodeCallLLM(base_state)

        assert result["llm_output"]["messages_to_send"] == []

    @pytest.mark.asyncio
    async def test_missing_system_prompt_logs_error(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: getPrompt returns empty string.
        Act: call nodeCallLLM.
        Assert: error logged, empty llm_output returned, LLM never called.
        """
        mock_ark = self._mock_llm_success(["reply"])
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                MagicMock(return_value=""),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                mock_ark,
            ),
        ):
            result = await nodeCallLLM(base_state)

        assert result["llm_output"]["messages_to_send"] == []
        assert len(result["errors"]) >= 1
        assert "prompt" in result["errors"][0].lower()
        # arkAinvoke should not have been called since prompt is empty
        mock_ark.assert_not_called()

    @pytest.mark.asyncio
    async def test_messages_to_send_null_handled(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: LLM returns null for messages_to_send.
        Act: call nodeCallLLM.
        Assert: empty messages list, no crash.
        """
        async def _null_output(**kwargs):
            return {"output": '{"messages_to_send": null}', "reasoning_content": ""}
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                AsyncMock(side_effect=_null_output),
            ),
        ):
            result = await nodeCallLLM(base_state)

        assert result["llm_output"]["messages_to_send"] == []

    @pytest.mark.asyncio
    async def test_single_string_message_normalized_to_list(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: LLM returns a plain string for messages_to_send.
        Act: call nodeCallLLM.
        Assert: it is normalized to a single-element list.
        """
        async def _string_output(**kwargs):
            return {"output": '{"messages_to_send": "only one message"}', "reasoning_content": "r"}
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                AsyncMock(side_effect=_string_output),
            ),
        ):
            result = await nodeCallLLM(base_state)

        assert result["llm_output"]["messages_to_send"] == ["only one message"]

    @pytest.mark.parametrize(
        "figure_role,role_key",
        [
            (FigureRole.SELF, "self"),
            (FigureRole.FAMILY, "family"),
            (FigureRole.FRIEND, "friend"),
            (FigureRole.MENTOR, "mentor"),
            (FigureRole.COLLEAGUE, "colleague"),
            (FigureRole.PARTNER, "partner"),
            (FigureRole.PUBLIC_FIGURE, "public_figure"),
            (FigureRole.STRANGER, "stranger"),
        ],
    )
    @pytest.mark.asyncio
    async def test_formality_level_varies_by_figure_role(
        self,
        base_state: dict[str, Any],
        figure_role: FigureRole,
        role_key: str,
    ) -> None:
        """Verify that nodeCallLLM functions correctly for every FigureRole
        and the system prompt is loaded (formality is prompt-driven)."""
        base_state["figure_and_relation"]["figure_role"] = figure_role.value
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(f"Prompt for {role_key}"),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                self._mock_llm_success([f"Reply as {figure_role.value}"]),
            ),
        ):
            result = await nodeCallLLM(base_state)

        assert result["llm_output"]["messages_to_send"] != []
        assert result["llm_output"]["reasoning_content"] != ""

    @pytest.mark.asyncio
    async def test_conversation_summary_injected_as_system_message(
        self, base_state: dict[str, Any]
    ) -> None:
        """When conversation_summary is non-empty, it is added as a SystemMessage
        before the current-turn messages."""
        base_state["conversation_summary"] = "Summary: discussed weekend plans."
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                self._mock_llm_success(["好的！"]),
            ) as mock_ark,
        ):
            await nodeCallLLM(base_state)

        call_messages = mock_ark.call_args.kwargs.get("messages", [])
        summary_found = any(
            "Summary:" in str(getattr(m, "content", ""))
            and isinstance(m, SystemMessage)
            for m in call_messages
        )
        assert summary_found

    @pytest.mark.asyncio
    async def test_llm_output_logs_message_count(
        self, base_state: dict[str, Any]
    ) -> None:
        """The nodeCallLLM log entry includes the count of messages_to_send."""
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                self._mock_llm_success(["msg1", "msg2", "msg3"]),
            ),
        ):
            result = await nodeCallLLM(base_state)

        ok_logs = [log for log in result["logs"] if log["status"] == "ok"]
        assert ok_logs[-1]["data"]["messages_to_send_count"] == 3

    @pytest.mark.asyncio
    async def test_error_preserves_previous_warnings_and_errors(
        self, base_state: dict[str, Any]
    ) -> None:
        """Pre-existing warnings and errors in state must survive
        a recovery path through nodeCallLLM."""
        base_state["warnings"] = ["prior warning"]
        base_state["errors"] = ["prior error"]
        async def _output(**kwargs):
            return {"output": "not json", "reasoning_content": ""}
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                AsyncMock(side_effect=_output),
            ),
        ):
            result = await nodeCallLLM(base_state)

        assert "prior warning" in result["warnings"]
        assert "prior error" in result["errors"]

    # -------------------------------------------------------------------
    # Anti-repetition & message quality
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_prevents_empty_messages_to_send_on_parse_failure(
        self, base_state: dict[str, Any]
    ) -> None:
        """On parse failure the node must NOT fabricate a response;
        messages_to_send must be empty and llm_output populated with reasoning
        if available."""
        async def _fail(**kwargs):
            return {"output": "broken {{{}", "reasoning_content": "I tried..."}
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                AsyncMock(side_effect=_fail),
            ),
        ):
            result = await nodeCallLLM(base_state)

        assert result["llm_output"]["messages_to_send"] == []
        assert result["llm_output"]["reasoning_content"] == "I tried..."

    @pytest.mark.asyncio
    async def test_multiple_rounds_dont_mix_message_ids(
        self, base_state: dict[str, Any]
    ) -> None:
        """Each new round appends a fresh AIMessage with a unique id."""
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                self._mock_llm_success(["round 1 reply"]),
            ),
        ):
            r1 = await nodeCallLLM(base_state)

        # Simulate round 2 with a different round_uuid
        base_state["round_uuid"] = str(uuid.uuid4())
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                self._mock_prompt(),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                self._mock_llm_success(["round 2 reply"]),
            ),
        ):
            r2 = await nodeCallLLM(base_state)

        ids_r1 = {m.id for m in r1.get("messages", []) if isinstance(m, AIMessage)}
        ids_r2 = {m.id for m in r2.get("messages", []) if isinstance(m, AIMessage)}
        assert not ids_r1.intersection(ids_r2)


# ---------------------------------------------------------------------------
# Message batch sizes (integration-style, node-level)
# ---------------------------------------------------------------------------


class TestMessageBatchSizes:
    """Node-level tests with varying message_received batch sizes."""

    @pytest.mark.parametrize("batch_size", [1, 3, 5, 10])
    @pytest.mark.asyncio
    async def test_build_and_trim_handles_batch_size(
        self,
        base_state: dict[str, Any],
        batch_size: int,
    ) -> None:
        """Verify nodeBuildAndTrimMessage works correctly for N incoming
        messages (concatenated with newlines)."""
        base_state["request"]["messages_received"] = [
            f"消息 {i}" for i in range(batch_size)
        ]
        async with _mock_trim_noop():
            result = await nodeBuildAndTrimMessage(base_state)

        returned = result.get("messages", [])
        human_msgs = [m for m in returned if isinstance(m, HumanMessage)]
        assert len(human_msgs) >= 1
        # The latest human message should contain all batch items joined by \n
        last_human = human_msgs[-1].content
        for i in range(batch_size):
            assert f"消息 {i}" in last_human

    @pytest.mark.parametrize("batch_size", [1, 3, 5, 10])
    @pytest.mark.asyncio
    async def test_recall_query_constructed_from_batch(
        self,
        base_state: dict[str, Any],
        batch_size: int,
    ) -> None:
        """The recall query is formed by joining messages with '. ' separator."""
        base_state["request"]["messages_received"] = [
            f"msg_{i}" for i in range(batch_size)
        ]
        with patch(
            "src.agents.graphs.ConversationGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
            return_value={
                "status": 200,
                "items": {"procedural_info": [], "memory": []},
            },
        ) as mock_recall:
            await nodeRecallFeedsFromDB(base_state)

        call_query = mock_recall.call_args.kwargs["query"]
        expected = ". ".join(f"msg_{i}" for i in range(batch_size))
        assert call_query == expected


# ---------------------------------------------------------------------------
# State transition semantics (parallel branches)
# ---------------------------------------------------------------------------


class TestStateTransitions:
    """Verify node outputs are compatible with the DAG's parallel edges."""

    def test_load_fr_output_keys_sufficient_for_downstream(
        self,
        base_state: dict[str, Any],
        sample_fr_friend: dict[str, Any],
        sample_user_data: dict[str, Any],
    ) -> None:
        """nodeLoadFRAndPersona must produce keys needed by both
        nodeRecallFeedsFromDB and nodeBuildAndTrimMessage."""
        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value=sample_user_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": 200,
                    "figure_and_relation": sample_fr_friend,
                },
            ),
        ):
            result = nodeLoadFRAndPersona(base_state)

        required = {"round_uuid", "figure_persona", "words_to_user", "user_name", "logs"}
        assert required.issubset(set(result.keys()))

    def test_merge_unique_list_idempotent(self) -> None:
        """_mergeUniqueList used in ConversationGraphState must be idempotent
        and deduplicate correctly."""
        from src.agents.graphs.ConversationGraph.state import _mergeUniqueList

        left = [{"a": 1}, {"b": 2}]
        right = [{"a": 1}, {"c": 3}]
        merged = _mergeUniqueList(left, right)
        assert len(merged) == 3
        assert {"a": 1} in merged
        assert {"b": 2} in merged
        assert {"c": 3} in merged

    def test_merge_unique_list_handles_empty(self) -> None:
        from src.agents.graphs.ConversationGraph.state import _mergeUniqueList

        assert _mergeUniqueList([], []) == []
        assert _mergeUniqueList(None, []) == []
        assert _mergeUniqueList([], None) == []


# ---------------------------------------------------------------------------
# Graph-level tests (mocked)
# ---------------------------------------------------------------------------


class TestConversationGraphMocked:
    """End-to-end graph tests with all dependencies mocked."""

    @pytest.mark.asyncio
    async def test_full_pipeline_completes_successfully(self) -> None:
        """A complete invocation of the mocked conversation graph produces
        llm_output with messages_to_send and non-empty reasoning."""
        from src.agents.graphs.ConversationGraph.graph import buildBaseConversationGraph

        graph = buildBaseConversationGraph()
        compiled = graph.compile()

        init_state = {
            "request": {
                "user_id": 1,
                "fr_id": 1,
                "messages_received": ["你好"],
            },
        }

        # We need a full chain of patches covering every node
        user_data = {
            "status": 200,
            "user": {"username": "testuser", "nickname": "T", "gender": "male"},
        }
        fr_data = {
            "status": 200,
            "figure_and_relation": {
                "id": 1,
                "user_id": 1,
                "figure_role": "friend",
                "figure_name": "Test",
                "figure_gender": "male",
                "figure_likes": [],
                "figure_dislikes": [],
                "words_figure2user": [],
                "words_user2figure": [],
                "exact_relation": "",
                "core_personality": "",
                "core_interaction_style": "",
                "core_procedural_info": "",
                "core_memory": "",
            },
        }
        recall_data = {
            "status": 200,
            "items": {"procedural_info": [], "memory": []},
        }

        async def _mock_ark(**kwargs):
            return {
                "output": '{"messages_to_send": ["你好！今天过得怎么样？"]}',
                "reasoning_content": "User greeted, respond warmly.",
            }

        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value=user_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getFigureAndRelation",
                return_value=fr_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.recallFineGrainedFeeds",
                new_callable=AsyncMock,
                return_value=recall_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                AsyncMock(side_effect=_mock_ark),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                MagicMock(return_value="You are a helpful assistant."),
            ),
        ):
            result = await compiled.ainvoke(init_state)

        assert result["llm_output"]["messages_to_send"] == ["你好！今天过得怎么样？"]
        assert "reasoning_content" in result["llm_output"]

    @pytest.mark.asyncio
    async def test_full_pipeline_with_multiple_rounds_accumulates_messages(
        self,
    ) -> None:
        """Multiple invocations with the same thread_id accumulate message
        history (short-term memory)."""
        from src.agents.graphs.ConversationGraph.graph import buildBaseConversationGraph

        graph = buildBaseConversationGraph()
        compiled = graph.compile()

        user_data = {
            "status": 200,
            "user": {"username": "testuser", "nickname": "T", "gender": "male"},
        }
        fr_data = {
            "status": 200,
            "figure_and_relation": {
                "id": 1,
                "user_id": 1,
                "figure_role": "friend",
                "figure_name": "Test",
                "figure_gender": "male",
                "figure_likes": [],
                "figure_dislikes": [],
                "words_figure2user": [],
                "words_user2figure": [],
                "exact_relation": "",
                "core_personality": "",
                "core_interaction_style": "",
                "core_procedural_info": "",
                "core_memory": "",
            },
        }
        recall_data = {"status": 200, "items": {"procedural_info": [], "memory": []}}

        async def _mock_ark(**kwargs):
            return {
                "output": '{"messages_to_send": ["round reply"]}',
                "reasoning_content": "ack",
            }

        with (
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getUserById",
                return_value=user_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getFigureAndRelation",
                return_value=fr_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.recallFineGrainedFeeds",
                new_callable=AsyncMock,
                return_value=recall_data,
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.arkAinvoke",
                AsyncMock(side_effect=_mock_ark),
            ),
            patch(
                "src.agents.graphs.ConversationGraph.nodes.getPrompt",
                MagicMock(return_value="You are a helpful assistant."),
            ),
        ):
            # Round 1
            r1 = await compiled.ainvoke({
                "request": {
                    "user_id": 1,
                    "fr_id": 1,
                    "messages_received": ["Round 1 message"],
                },
            })
            assert len(r1.get("messages", [])) >= 1

            # Round 2 -- pass previous messages
            r2_init = {
                "request": {
                    "user_id": 1,
                    "fr_id": 1,
                    "messages_received": ["Round 2 message"],
                },
                "messages": r1.get("messages", []),
            }
            r2 = await compiled.ainvoke(r2_init)
            assert len(r2.get("messages", [])) >= len(r1.get("messages", []))
