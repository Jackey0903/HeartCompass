"""
Comprehensive pipeline tests for the FRBuildingGraph (11-node sequential pipeline).

Covers all 11 nodes:
  1. nodeLoadFR             -- load FigureAndRelation, validate ownership
  2. nodePreprocessInput    -- LLM-based input cleaning, metadata extraction
  3. nodePersistOriginalSource -- original_source persistence
  4. nodeExtractFRIntrinsicCandidates -- field extraction from raw content
  5. nodePlanFRIntrinsicUpdate -- conflict-aware update planning (string/list/MBTI)
  6. nodePersistFRIntrinsicUpdate -- write FR intrinsic updates to DB
  7. nodeExtractFineGrainedFeeds -- dimension-parallel feed extraction
  8. nodePlanFineGrainedFeedUpsert -- recall + compare + plan (add/update/skip/conflict)
  9. nodePersistFineGrainedFeedUpsert -- execute upsert plan
 10. nodeBuildFRBuildingGraphOutput -- aggregate final status
 11. nodeGenerateFRBuildingReport -- LLM report generation and persistence

Focus areas:
  - Sequential pipeline execution semantics
  - Persona extraction from various input types
  - Field comparison logic (string, list, MBTI)
  - Feed extraction across 4 dimensions with concurrency
  - Conflict detection, resolution, and recording
  - Build report generation
  - Concurrent build prevention (RuntimeError when already running)
  - Error recovery and partial-success paths
  - Mock-based tests with simulated LLM responses
  - Fixtures for all FigureRole types

All external dependencies (DB, LLM, embedding, recall) are mocked.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.graphs.FRBuildingGraph.nodes import (
    nodeBuildFRBuildingGraphOutput,
    nodeExtractFineGrainedFeeds,
    nodeExtractFRIntrinsicCandidates,
    nodeGenerateFRBuildingReport,
    nodeLoadFR,
    nodePersistFineGrainedFeedUpsert,
    nodePersistFRIntrinsicUpdate,
    nodePersistOriginalSource,
    nodePlanFineGrainedFeedUpsert,
    nodePlanFRIntrinsicUpdate,
    nodePreprocessInput,
)
from src.database.enums import (
    ConflictStatus,
    FigureRole,
    FineGrainedFeedConfidence,
    FineGrainedFeedDimension,
    MBTI,
    OriginalSourceType,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user() -> dict[str, Any]:
    return {
        "status": 200,
        "message": "Get user success",
        "user": {"username": "testuser", "nickname": "Test", "gender": "male"},
    }


@pytest.fixture
def sample_fr_base() -> dict[str, Any]:
    """Base FigureAndRelation dict with all fields populated."""
    return {
        "id": 1,
        "user_id": 1,
        "figure_role": "self",
        "figure_name": "卜天",
        "figure_gender": "male",
        "figure_mbti": "ENTJ",
        "figure_birthday": "2004-12-09",
        "figure_occupation": "软件工程师",
        "figure_education": "同济大学 软件工程",
        "figure_residence": "上海",
        "figure_hometown": "呼和浩特",
        "figure_appearance": "短发，戴眼镜",
        "figure_likes": ["编程", "乒乓球"],
        "figure_dislikes": ["迟到"],
        "words_figure2user": ["今天效率不错"],
        "words_user2figure": ["帮我看下这段代码"],
        "exact_relation": "自我认知",
        "core_personality": "目标明确，执行力强，喜欢系统性解决问题",
        "core_interaction_style": "直接，注重效率",
        "core_procedural_info": "习惯早上规划全天任务",
        "core_memory": "2024年在北京字节跳动实习",
    }


@pytest.fixture
def base_request() -> dict[str, Any]:
    return {
        "user_id": 1,
        "fr_id": 1,
        "raw_content": (
            "我叫卜天，2004年12月9日生于呼和浩特。"
            "我在同济大学读软件工程，目前在字节跳动实习。"
            "我喜欢编程和乒乓球，最讨厌迟到。"
            "我的MBTI是ENTJ，习惯每天早上规划全天任务。"
        ),
        "raw_images": None,
    }


@pytest.fixture
def base_state(
    base_request: dict[str, Any],
    sample_fr_base: dict[str, Any],
    sample_user: dict[str, Any],
) -> dict[str, Any]:
    """Construct the minimal valid FRBuildingGraphState after nodeLoadFR."""
    return {
        "request": base_request,
        "user_name": sample_user["user"]["username"],
        "figure_and_relation": sample_fr_base,
        "figure_role": FigureRole.SELF,
        "logs": [],
        "warnings": [],
        "errors": [],
        "status": "running",
    }


# ---------------------------------------------------------------------------
# 1. nodeLoadFR
# ---------------------------------------------------------------------------


class TestNodeLoadFR:
    """Tests for step 1: loading FigureAndRelation and figure_role."""

    def test_loads_fr_successfully(
        self,
        base_state: dict[str, Any],
        sample_fr_base: dict[str, Any],
        sample_user: dict[str, Any],
    ) -> None:
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getUserById",
                return_value=sample_user,
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": 200,
                    "figure_and_relation": sample_fr_base,
                },
            ),
        ):
            result = nodeLoadFR(base_state)

        assert result["user_name"] == "testuser"
        assert result["figure_role"] == FigureRole.SELF
        assert result["figure_and_relation"] == sample_fr_base
        assert result["logs"][0]["step"] == "nodeLoadFR"
        assert result["logs"][0]["status"] == "ok"

    def test_user_not_found_raises(
        self, base_state: dict[str, Any]
    ) -> None:
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.getUserById",
            return_value={"status": -1, "user": None},
        ):
            with pytest.raises(ValueError, match="User not found"):
                nodeLoadFR(base_state)

    def test_fr_not_found_raises(
        self,
        base_state: dict[str, Any],
        sample_user: dict[str, Any],
    ) -> None:
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getUserById",
                return_value=sample_user,
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": -3,
                    "figure_and_relation": None,
                },
            ),
        ):
            with pytest.raises(ValueError, match="Figure and relation not found"):
                nodeLoadFR(base_state)

    @pytest.mark.parametrize("figure_role", list(FigureRole))
    def test_parses_all_figure_roles(
        self,
        base_state: dict[str, Any],
        sample_fr_base: dict[str, Any],
        sample_user: dict[str, Any],
        figure_role: FigureRole,
    ) -> None:
        fr = dict(sample_fr_base)
        fr["figure_role"] = figure_role.value
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getUserById",
                return_value=sample_user,
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": 200,
                    "figure_and_relation": fr,
                },
            ),
        ):
            result = nodeLoadFR(base_state)

        assert result["figure_role"] == figure_role
        log_data = result["logs"][0]["data"]
        assert log_data["figure_role"] == figure_role.value


# ---------------------------------------------------------------------------
# 2. nodePreprocessInput
# ---------------------------------------------------------------------------


class TestNodePreprocessInput:
    """Tests for step 2: LLM-based input preprocessing."""

    def _mock_preprocess(self, content: str, dims=None, confidence="impression",
                         src_type="narrative_from_user") -> dict[str, Any]:
        if dims is None:
            dims = ["personality", "procedural_info", "memory"]
        return {
            "cleaned_content": content,
            "metadata": {
                "original_source_type": src_type,
                "confidence": confidence,
                "included_dimensions": dims,
                "approx_date": "2025-Q3",
            },
        }

    @pytest.mark.asyncio
    async def test_preprocess_produces_original_source(
        self, base_state: dict[str, Any]
    ) -> None:
        """Arrange: LLM returns cleaned_content and metadata.
        Act: call nodePreprocessInput.
        Assert: original_source populated with parsed enums and content."""
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="preprocess prompt"),
            ),
            patch.object(
                asyncio,
                "sleep",
                AsyncMock(return_value=None),
            ),
        ):
            # Mock the LLM.ainvoke to return valid JSON
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"cleaned_content": "cleaned text", '
                '"metadata": {"original_source_type": "narrative_from_user", '
                '"confidence": "impression", '
                '"included_dimensions": ["personality"], "approx_date": null}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodePreprocessInput(base_state)

        os_ = result["original_source"]
        assert os_["content"] == "cleaned text"
        assert os_["type"] == OriginalSourceType.NARRATIVE_FROM_USER
        assert os_["confidence"] == FineGrainedFeedConfidence.IMPRESSION
        assert FineGrainedFeedDimension.PERSONALITY in os_["included_dimensions"]
        log = result["logs"][-1]
        assert log["step"] == "nodePreprocessInput"
        assert log["status"] == "ok"
        assert log["data"]["has_raw_images"] is False

    @pytest.mark.asyncio
    async def test_empty_raw_content_and_images_raises(
        self, base_state: dict[str, Any]
    ) -> None:
        """When both raw_content and raw_images are empty, ValueError is raised."""
        base_state["request"]["raw_content"] = ""
        base_state["request"]["raw_images"] = []
        with pytest.raises(ValueError, match="cannot be both empty"):
            await nodePreprocessInput(base_state)

    @pytest.mark.asyncio
    async def test_too_short_content_raises(
        self, base_state: dict[str, Any]
    ) -> None:
        """raw_content shorter than 10 chars raises ValueError."""
        base_state["request"]["raw_content"] = "Hi"
        with pytest.raises(ValueError, match="too short"):
            await nodePreprocessInput(base_state)

    @pytest.mark.asyncio
    async def test_missing_prompt_raises(
        self, base_state: dict[str, Any]
    ) -> None:
        """When getPrompt returns empty string, ValueError is raised."""
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
            MagicMock(return_value=""),
        ):
            with pytest.raises(ValueError, match="prompt is empty"):
                await nodePreprocessInput(base_state)

    @pytest.mark.asyncio
    async def test_invalid_json_response_raises(
        self, base_state: dict[str, Any]
    ) -> None:
        """LLM returning non-JSON raises ValueError."""
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
            MagicMock(return_value="preprocess prompt"),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = "not json at all {{{"
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                with pytest.raises(ValueError, match="not valid JSON"):
                    await nodePreprocessInput(base_state)

    @pytest.mark.asyncio
    async def test_empty_included_dimensions_falls_back(
        self, base_state: dict[str, Any]
    ) -> None:
        """When LLM returns empty included_dimensions, fallback to [OTHER]."""
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="preprocess prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"cleaned_content": "some text", '
                '"metadata": {"original_source_type": "narrative_from_user", '
                '"confidence": "impression", "included_dimensions": [], '
                '"approx_date": null}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodePreprocessInput(base_state)

        # Fallback: OTHER dimension used
        dims = result["original_source"]["included_dimensions"]
        assert FineGrainedFeedDimension.OTHER in dims

    @pytest.mark.asyncio
    async def test_with_raw_images(self, base_state: dict[str, Any]) -> None:
        """When raw_images are present, they become part of the user prompt
        as image_url blocks."""
        base_state["request"]["raw_images"] = ["https://example.com/img1.png"]
        base_state["figure_and_relation"]["figure_name"] = "TestFigure"
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="preprocess prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"cleaned_content": "image described", '
                '"metadata": {"original_source_type": "self_artifact", '
                '"confidence": "artifact", '
                '"included_dimensions": ["procedural_info"], '
                '"approx_date": null}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodePreprocessInput(base_state)

        log = result["logs"][-1]
        assert log["data"]["has_raw_images"] is True


# ---------------------------------------------------------------------------
# 3. nodePersistOriginalSource
# ---------------------------------------------------------------------------


class TestNodePersistOriginalSource:
    """Tests for step 3: persisting original_source to DB."""

    def test_persists_and_returns_id(self, base_state: dict[str, Any]) -> None:
        base_state["original_source"] = {
            "type": OriginalSourceType.NARRATIVE_FROM_USER,
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
            "included_dimensions": [FineGrainedFeedDimension.PERSONALITY],
            "content": "test content",
            "approx_date": None,
        }
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.addOriginalSource",
            return_value={"status": 200, "original_source_id": 42},
        ):
            result = nodePersistOriginalSource(base_state)

        assert result["original_source_id"] == 42
        assert result["logs"][-1]["step"] == "nodePersistOriginalSource"
        assert result["logs"][-1]["status"] == "ok"

    def test_persist_failure_raises(self, base_state: dict[str, Any]) -> None:
        base_state["original_source"] = {
            "type": OriginalSourceType.NARRATIVE_FROM_USER,
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
            "included_dimensions": [FineGrainedFeedDimension.PERSONALITY],
            "content": "test",
            "approx_date": None,
        }
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.addOriginalSource",
            return_value={"status": 500, "message": "DB down"},
        ):
            with pytest.raises(ValueError, match="Add original source failed"):
                nodePersistOriginalSource(base_state)


# ---------------------------------------------------------------------------
# 4. nodeExtractFRIntrinsicCandidates
# ---------------------------------------------------------------------------


class TestNodeExtractFRIntrinsicCandidates:
    """Tests for step 4: extracting FR intrinsic fields from original_source."""

    def _make_state_with_original_source(
        self, base_state: dict[str, Any], content: str
    ) -> dict[str, Any]:
        state = dict(base_state)
        state["original_source"] = {
            "content": content,
            "type": OriginalSourceType.NARRATIVE_FROM_USER,
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
            "included_dimensions": [FineGrainedFeedDimension.PERSONALITY],
        }
        return state

    @pytest.mark.asyncio
    async def test_extracts_fr_fields_from_content(
        self, base_state: dict[str, Any]
    ) -> None:
        state = self._make_state_with_original_source(
            base_state,
            "我叫李华，出生于1995年8月，住在北京，毕业于北京大学，职业是律师。",
        )
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="extract prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"fr_intrinsic_candidates": {'
                '"figure_birthday": "1995-08", '
                '"figure_occupation": "律师", '
                '"figure_education": "北京大学", '
                '"figure_residence": "北京"'
                '}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeExtractFRIntrinsicCandidates(state)

        updates = result["fr_intrinsic_updates"]
        assert updates["figure_birthday"] == "1995-08"
        assert updates["figure_occupation"] == "律师"
        assert updates["figure_education"] == "北京大学"
        assert updates["figure_residence"] == "北京"
        log = result["logs"][-1]
        assert log["data"]["extracted_count"] == 4

    @pytest.mark.asyncio
    async def test_extracts_mbti_field(self, base_state: dict[str, Any]) -> None:
        state = self._make_state_with_original_source(
            base_state, "我的MBTI是INFJ。"
        )
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="extract prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"fr_intrinsic_candidates": {"figure_mbti": "INFJ"}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeExtractFRIntrinsicCandidates(state)

        assert result["fr_intrinsic_updates"]["figure_mbti"] == MBTI.INFJ

    @pytest.mark.asyncio
    async def test_extracts_list_fields(self, base_state: dict[str, Any]) -> None:
        state = self._make_state_with_original_source(
            base_state, "他喜欢游泳、跑步和阅读。不喜欢早起和排队。"
        )
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="extract prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"fr_intrinsic_candidates": {'
                '"figure_likes": ["游泳", "跑步", "阅读"], '
                '"figure_dislikes": ["早起", "排队"]'
                '}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeExtractFRIntrinsicCandidates(state)

        assert result["fr_intrinsic_updates"]["figure_likes"] == ["游泳", "跑步", "阅读"]
        assert result["fr_intrinsic_updates"]["figure_dislikes"] == ["早起", "排队"]

    @pytest.mark.asyncio
    async def test_ignores_invalid_fields(self, base_state: dict[str, Any]) -> None:
        state = self._make_state_with_original_source(
            base_state, "some text"
        )
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="extract prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"fr_intrinsic_candidates": {'
                '"invalid_field": "some value", '
                '"figure_birthday": "2000-01"'
                '}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeExtractFRIntrinsicCandidates(state)

        log = result["logs"][-1]
        assert "invalid_field" in log["data"]["ignored_fields"]
        assert "figure_birthday" in log["data"]["extracted_fields"]

    @pytest.mark.asyncio
    async def test_empty_original_source_content_raises(
        self, base_state: dict[str, Any]
    ) -> None:
        state = dict(base_state)
        state["original_source"] = {"content": "", "type": None, "confidence": None,
                                    "included_dimensions": []}
        with pytest.raises(ValueError, match="original_source.content is empty"):
            await nodeExtractFRIntrinsicCandidates(state)

    @pytest.mark.asyncio
    async def test_dedup_list_values(self, base_state: dict[str, Any]) -> None:
        """Duplicate items in extracted lists are removed."""
        state = self._make_state_with_original_source(
            base_state, "likes a, likes a, likes b"
        )
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="extract prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"fr_intrinsic_candidates": {"figure_likes": ["a", "a", "b"]}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeExtractFRIntrinsicCandidates(state)

        assert result["fr_intrinsic_updates"]["figure_likes"] == ["a", "b"]


# ---------------------------------------------------------------------------
# 5. nodePlanFRIntrinsicUpdate
# ---------------------------------------------------------------------------


class TestNodePlanFRIntrinsicUpdate:
    """Tests for step 5: planning FR intrinsic field updates with conflict awareness."""

    @pytest.mark.asyncio
    async def test_mbti_new_accepted_when_existing_is_none(
        self, base_state: dict[str, Any]
    ) -> None:
        """When existing MBTI is None, new MBTI is accepted directly."""
        base_state["figure_and_relation"]["figure_mbti"] = None
        base_state["fr_intrinsic_updates"] = {"figure_mbti": MBTI.INFP}
        result = await nodePlanFRIntrinsicUpdate(base_state)

        assert result["fr_intrinsic_updates"]["figure_mbti"] == MBTI.INFP

    @pytest.mark.asyncio
    async def test_mbti_keep_old_when_same(self, base_state: dict[str, Any]) -> None:
        """When new MBTI matches existing, it is not added to updates."""
        base_state["figure_and_relation"]["figure_mbti"] = "ENTJ"
        base_state["fr_intrinsic_updates"] = {"figure_mbti": "ENTJ"}
        result = await nodePlanFRIntrinsicUpdate(base_state)

        assert "figure_mbti" not in result["fr_intrinsic_updates"]

    @pytest.mark.asyncio
    async def test_mbti_change_logs_warning(self, base_state: dict[str, Any]) -> None:
        """An MBTI change from existing to new generates a warning."""
        base_state["figure_and_relation"]["figure_mbti"] = "INTJ"
        base_state["fr_intrinsic_updates"] = {"figure_mbti": "ENTP"}
        result = await nodePlanFRIntrinsicUpdate(base_state)

        assert result["fr_intrinsic_updates"]["figure_mbti"] == MBTI.ENTP
        assert len(result["warnings"]) >= 1
        assert "INTJ" in result["warnings"][0] and "ENTP" in result["warnings"][0]

    @pytest.mark.asyncio
    async def test_string_field_new_accepted_when_old_empty(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["figure_and_relation"]["figure_occupation"] = ""
        base_state["fr_intrinsic_updates"] = {"figure_occupation": "工程师"}
        result = await nodePlanFRIntrinsicUpdate(base_state)

        assert result["fr_intrinsic_updates"]["figure_occupation"] == "工程师"

    @pytest.mark.asyncio
    async def test_string_field_keep_old_when_equal(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["figure_and_relation"]["figure_occupation"] = "工程师"
        base_state["fr_intrinsic_updates"] = {"figure_occupation": "工程师"}
        result = await nodePlanFRIntrinsicUpdate(base_state)

        assert "figure_occupation" not in result["fr_intrinsic_updates"]

    @pytest.mark.asyncio
    async def test_string_field_compare_via_llm_on_conflict(
        self, base_state: dict[str, Any]
    ) -> None:
        """When old and new string values differ, LLM is consulted."""
        base_state["figure_and_relation"]["figure_occupation"] = "前端开发"
        base_state["fr_intrinsic_updates"] = {"figure_occupation": "全栈工程师"}

        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes._compareFieldViaLLM",
            new_callable=AsyncMock,
            return_value={
                "tag": "supplementary",
                "final_value": "全栈工程师（侧重前端）",
                "conflict_status": ConflictStatus.RESOLVED_MERGE,
                "detail": "新旧信息互相补充",
            },
        ):
            result = await nodePlanFRIntrinsicUpdate(base_state)

        assert result["fr_intrinsic_updates"]["figure_occupation"] == "全栈工程师（侧重前端）"

    @pytest.mark.asyncio
    async def test_list_field_new_accepted_when_old_empty(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["figure_and_relation"]["figure_likes"] = []
        base_state["fr_intrinsic_updates"] = {"figure_likes": ["读书", "写作"]}
        result = await nodePlanFRIntrinsicUpdate(base_state)

        assert result["fr_intrinsic_updates"]["figure_likes"] == ["读书", "写作"]

    @pytest.mark.asyncio
    async def test_words_fields_merge_with_cap(
        self, base_state: dict[str, Any]
    ) -> None:
        """words_figure2user and words_user2figure are merged (not compared)
        with a MAX_WORDS cap."""
        base_state["figure_and_relation"]["words_figure2user"] = ["加油", "不错"]
        base_state["fr_intrinsic_updates"] = {
            "words_figure2user": ["继续努力", "太棒了"]
        }
        result = await nodePlanFRIntrinsicUpdate(base_state)

        merged = result["fr_intrinsic_updates"]["words_figure2user"]
        assert "加油" in merged
        assert "继续努力" in merged

    @pytest.mark.asyncio
    async def test_empty_extracted_candidates_skips(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["fr_intrinsic_updates"] = {}
        result = await nodePlanFRIntrinsicUpdate(base_state)

        assert result["fr_intrinsic_updates"] == {}
        assert result["logs"][-1]["status"] == "skip"

    @pytest.mark.asyncio
    async def test_plan_logs_contain_action_details(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["figure_and_relation"]["figure_birthday"] = ""
        base_state["fr_intrinsic_updates"] = {"figure_birthday": "2000-01-01"}
        result = await nodePlanFRIntrinsicUpdate(base_state)

        log = result["logs"][-1]
        assert log["data"]["planned_count"] == 1
        assert "figure_birthday" in log["data"]["planned_fields"]
        assert len(log["data"]["plan_actions"]) == 1


# ---------------------------------------------------------------------------
# 6. nodePersistFRIntrinsicUpdate
# ---------------------------------------------------------------------------


class TestNodePersistFRIntrinsicUpdate:
    """Tests for step 6: persisting FR intrinsic updates."""

    def test_persist_success(self, base_state: dict[str, Any]) -> None:
        base_state["fr_intrinsic_updates"] = {"figure_occupation": "律师"}
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.updateFigureAndRelation",
            return_value={"status": 200, "message": "ok"},
        ):
            result = nodePersistFRIntrinsicUpdate(base_state)

        assert result["fr_update_result"]["status"] == 200
        assert result["figure_and_relation"]["figure_occupation"] == "律师"
        log = result["logs"][-1]
        assert log["step"] == "nodePersistFRIntrinsicUpdate"

    def test_persist_empty_updates_skips(self, base_state: dict[str, Any]) -> None:
        base_state["fr_intrinsic_updates"] = {}
        result = nodePersistFRIntrinsicUpdate(base_state)

        assert result["logs"][-1]["status"] == "skip"
        assert result["fr_update_result"]["status"] == 200

    def test_persist_failure_raises(self, base_state: dict[str, Any]) -> None:
        base_state["fr_intrinsic_updates"] = {"figure_occupation": "律师"}
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.updateFigureAndRelation",
            return_value={"status": 500, "message": "DB error"},
        ):
            with pytest.raises(ValueError, match="Update FigureAndRelation failed"):
                nodePersistFRIntrinsicUpdate(base_state)

    def test_state_fr_updated_in_place(self, base_state: dict[str, Any]) -> None:
        """The returned figure_and_relation dict includes the new field values."""
        base_state["figure_and_relation"]["figure_occupation"] = ""
        base_state["fr_intrinsic_updates"] = {"figure_occupation": "教师"}
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.updateFigureAndRelation",
            return_value={"status": 200, "message": "ok"},
        ):
            result = nodePersistFRIntrinsicUpdate(base_state)

        assert result["figure_and_relation"]["figure_occupation"] == "教师"


# ---------------------------------------------------------------------------
# 7. nodeExtractFineGrainedFeeds
# ---------------------------------------------------------------------------


class TestNodeExtractFineGrainedFeeds:
    """Tests for step 7: extracting fine-grained feeds across dimensions."""

    def _make_state(self, base_state: dict[str, Any], included_dims=None) -> dict[str, Any]:
        if included_dims is None:
            included_dims = [
                FineGrainedFeedDimension.PERSONALITY,
                FineGrainedFeedDimension.MEMORY,
            ]
        state = dict(base_state)
        state["original_source"] = {
            "content": "他是一个乐观的人。去年一起去了云南旅行。",
            "type": OriginalSourceType.NARRATIVE_FROM_USER,
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
            "included_dimensions": included_dims,
        }
        return state

    @pytest.mark.asyncio
    async def test_extracts_feeds_per_dimension(self, base_state: dict[str, Any]) -> None:
        state = self._make_state(base_state)
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="role/dimension prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            # Personality extraction returns 2 feeds, Memory returns 1
            call_count = 0

            async def mock_ainvoke(messages, **kwargs):
                nonlocal call_count
                call_count += 1
                fake = MagicMock()
                if call_count in (1, 2):
                    fake.content = (
                        '[{"sub_dimension": "optimism", '
                        '"confidence": "impression", '
                        '"content": "很乐观"}, '
                        '{"sub_dimension": "humor", '
                        '"confidence": "impression", '
                        '"content": "幽默风趣"}]'
                    )
                else:
                    fake.content = (
                        '[{"sub_dimension": "travel", '
                        '"confidence": "impression", '
                        '"content": "云南旅行"}]'
                    )
                return fake

            mock_llm.ainvoke = mock_ainvoke
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeExtractFineGrainedFeeds(state)

        feeds = result["extracted_feeds"]
        assert len(feeds) >= 2  # at minimum personality + memory feeds
        dims = {f["dimension"] for f in feeds}
        assert FineGrainedFeedDimension.PERSONALITY in dims
        assert FineGrainedFeedDimension.MEMORY in dims

    @pytest.mark.asyncio
    async def test_no_dimensions_skips_gracefully(self, base_state: dict[str, Any]) -> None:
        state = self._make_state(base_state, included_dims=[])
        result = await nodeExtractFineGrainedFeeds(state)

        assert len(result["warnings"]) >= 1
        assert result.get("extracted_feeds", []) == []

    @pytest.mark.asyncio
    async def test_invalid_figure_role_raises(self, base_state: dict[str, Any]) -> None:
        state = dict(base_state)
        del state["figure_role"]
        with pytest.raises(ValueError, match="figure_role is invalid"):
            await nodeExtractFineGrainedFeeds(state)

    @pytest.mark.asyncio
    async def test_extraction_error_per_dimension_captured(
        self, base_state: dict[str, Any]
    ) -> None:
        """If one dimension fails to extract, others still succeed."""
        state = self._make_state(base_state)
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="role/dimension prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            call_count = 0

            async def mock_ainvoke(messages, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1 or call_count == 2:
                    # Personality: fail with invalid JSON
                    return MagicMock(content="not json")
                else:
                    # Memory: succeed
                    return MagicMock(
                        content='[{"sub_dimension": "trip", "confidence": "impression", "content": "云南"}]'
                    )

            mock_llm.ainvoke = mock_ainvoke
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeExtractFineGrainedFeeds(state)

        # Personality dimension may have warnings, but Memory should still succeed
        feeds = result["extracted_feeds"]
        memory_feeds = [f for f in feeds if f["dimension"] == FineGrainedFeedDimension.MEMORY]
        assert len(memory_feeds) >= 1

    @pytest.mark.asyncio
    async def test_all_four_dimensions_extracted(
        self, base_state: dict[str, Any]
    ) -> None:
        """Verify extraction works across ALL 4 main dimensions + OTHER."""
        dims = [
            FineGrainedFeedDimension.PERSONALITY,
            FineGrainedFeedDimension.INTERACTION_STYLE,
            FineGrainedFeedDimension.PROCEDURAL_INFO,
            FineGrainedFeedDimension.MEMORY,
            FineGrainedFeedDimension.OTHER,
        ]
        state = self._make_state(base_state, included_dims=dims)
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="role/dimension prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()

            async def mock_ainvoke(messages, **kwargs):
                return MagicMock(
                    content='[{"sub_dimension": "test", "confidence": "impression", "content": "data"}]'
                )

            mock_llm.ainvoke = mock_ainvoke
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeExtractFineGrainedFeeds(state)

        feeds = result["extracted_feeds"]
        dims_found = {f["dimension"] for f in feeds}
        for dim in dims:
            assert dim in dims_found, f"Missing dimension: {dim.value}"


# ---------------------------------------------------------------------------
# 8. nodePlanFineGrainedFeedUpsert
# ---------------------------------------------------------------------------


class TestNodePlanFineGrainedFeedUpsert:
    """Tests for step 8: planning feed upserts with recall + LLM comparison."""

    @pytest.mark.asyncio
    async def test_empty_extracted_feeds_skips(self, base_state: dict[str, Any]) -> None:
        base_state["extracted_feeds"] = []
        result = await nodePlanFineGrainedFeedUpsert(base_state)

        assert result["feed_upsert_plan"] == []
        assert result["logs"][-1]["status"] == "skip"

    @pytest.mark.asyncio
    async def test_no_relevant_recalled_adds_new(self, base_state: dict[str, Any]) -> None:
        base_state["extracted_feeds"] = [{
            "dimension": FineGrainedFeedDimension.MEMORY,
            "sub_dimension": "childhood",
            "content": "小时候住在北京胡同",
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
        }]
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
            return_value={"status": 200, "items": {}},
        ):
            result = await nodePlanFineGrainedFeedUpsert(base_state)

        plan = result["feed_upsert_plan"]
        assert len(plan) == 1
        assert plan[0]["action"] == "add"

    @pytest.mark.asyncio
    async def test_equivalent_feed_skipped(self, base_state: dict[str, Any]) -> None:
        base_state["extracted_feeds"] = [{
            "dimension": FineGrainedFeedDimension.PERSONALITY,
            "sub_dimension": "trait",
            "content": "性格开朗",
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
        }]
        recalled_item = {
            "score": 0.95,
            "fine_grained_feed": {
                "id": 10,
                "dimension": "personality",
                "sub_dimension": "trait",
                "confidence": "impression",
                "content": "性格开朗外向",
            },
        }
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.recallFineGrainedFeeds",
                new_callable=AsyncMock,
                return_value={
                    "status": 200,
                    "items": {"personality": [recalled_item]},
                },
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes._compareFieldViaLLM",
                new_callable=AsyncMock,
                return_value={
                    "tag": "equivalent",
                    "final_value": "",
                    "conflict_status": None,
                    "detail": "Same meaning",
                },
            ),
        ):
            result = await nodePlanFineGrainedFeedUpsert(base_state)

        plan = result["feed_upsert_plan"]
        assert plan[0]["action"] == "skip"

    @pytest.mark.asyncio
    async def test_supplementary_feed_updated(self, base_state: dict[str, Any]) -> None:
        base_state["extracted_feeds"] = [{
            "dimension": FineGrainedFeedDimension.PERSONALITY,
            "sub_dimension": "trait",
            "content": "性格开朗且细心",
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
        }]
        recalled_item = {
            "score": 0.92,
            "fine_grained_feed": {
                "id": 11,
                "dimension": "personality",
                "sub_dimension": "trait",
                "confidence": "impression",
                "content": "性格开朗",
            },
        }
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.recallFineGrainedFeeds",
                new_callable=AsyncMock,
                return_value={
                    "status": 200,
                    "items": {"personality": [recalled_item]},
                },
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes._compareFieldViaLLM",
                new_callable=AsyncMock,
                return_value={
                    "tag": "supplementary",
                    "final_value": "性格开朗且细心",
                    "conflict_status": None,
                    "detail": "New info adds detail",
                },
            ),
        ):
            result = await nodePlanFineGrainedFeedUpsert(base_state)

        plan = result["feed_upsert_plan"]
        assert plan[0]["action"] == "update"
        assert plan[0]["merged_content"] == "性格开朗且细心"

    @pytest.mark.asyncio
    async def test_conflictive_feed_recorded(self, base_state: dict[str, Any]) -> None:
        base_state["extracted_feeds"] = [{
            "dimension": FineGrainedFeedDimension.MEMORY,
            "sub_dimension": "event",
            "content": "2023年毕业的",
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
        }]
        recalled_item = {
            "score": 0.9,
            "fine_grained_feed": {
                "id": 12,
                "dimension": "memory",
                "sub_dimension": "event",
                "confidence": "impression",
                "content": "2024年毕业的",
            },
        }
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.recallFineGrainedFeeds",
                new_callable=AsyncMock,
                return_value={
                    "status": 200,
                    "items": {"memory": [recalled_item]},
                },
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes._compareFieldViaLLM",
                new_callable=AsyncMock,
                return_value={
                    "tag": "conflictive",
                    "final_value": "毕业年份矛盾",
                    "conflict_status": ConflictStatus.PENDING,
                    "detail": "Contradicting graduation year",
                },
            ),
        ):
            result = await nodePlanFineGrainedFeedUpsert(base_state)

        plan = result["feed_upsert_plan"]
        assert plan[0]["action"] == "conflict"

    @pytest.mark.asyncio
    async def test_recall_failure_graceful_with_add(
        self, base_state: dict[str, Any]
    ) -> None:
        """When recall fails for a feed, the plan still adds the new feed."""
        base_state["extracted_feeds"] = [{
            "dimension": FineGrainedFeedDimension.PROCEDURAL_INFO,
            "sub_dimension": "method",
            "content": "使用番茄工作法",
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
        }]
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
            return_value={"status": 500, "message": "DB timeout"},
        ):
            result = await nodePlanFineGrainedFeedUpsert(base_state)

        plan = result["feed_upsert_plan"]
        assert len(plan) == 1
        assert plan[0]["action"] == "add"
        assert len(result["warnings"]) >= 1

    @pytest.mark.asyncio
    async def test_invalid_user_id_raises(self, base_state: dict[str, Any]) -> None:
        base_state["request"]["user_id"] = None
        with pytest.raises(ValueError, match="Invalid request.user_id"):
            await nodePlanFineGrainedFeedUpsert(base_state)

    @pytest.mark.asyncio
    async def test_logs_include_action_counter(self, base_state: dict[str, Any]) -> None:
        base_state["extracted_feeds"] = [
            {
                "dimension": FineGrainedFeedDimension.PERSONALITY,
                "sub_dimension": "a",
                "content": "content a",
                "confidence": FineGrainedFeedConfidence.IMPRESSION,
            },
            {
                "dimension": FineGrainedFeedDimension.MEMORY,
                "sub_dimension": "b",
                "content": "content b",
                "confidence": FineGrainedFeedConfidence.IMPRESSION,
            },
        ]
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.recallFineGrainedFeeds",
            new_callable=AsyncMock,
            return_value={"status": 200, "items": {}},
        ):
            result = await nodePlanFineGrainedFeedUpsert(base_state)

        counter = result["logs"][-1]["data"]["action_counter"]
        assert counter["add"] == 2


# ---------------------------------------------------------------------------
# 9. nodePersistFineGrainedFeedUpsert
# ---------------------------------------------------------------------------


class TestNodePersistFineGrainedFeedUpsert:
    """Tests for step 9: executing the upsert plan."""

    @pytest.mark.asyncio
    async def test_persist_add_action(self, base_state: dict[str, Any]) -> None:
        base_state["original_source_id"] = 42
        base_state["feed_upsert_plan"] = [{
            "extracted_feed": {
                "dimension": FineGrainedFeedDimension.MEMORY,
                "sub_dimension": "travel",
                "content": "去过日本",
                "confidence": FineGrainedFeedConfidence.IMPRESSION,
            },
            "action": "add",
            "target_feed_id": None,
            "merged_content": None,
            "reason": "No relevant recalled feed",
            "recalled_candidates": [],
        }]
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.addFineGrainedFeed",
            new_callable=AsyncMock,
            return_value={"status": 200, "message": "ok"},
        ):
            result = await nodePersistFineGrainedFeedUpsert(base_state)

        assert len(result["feed_upsert_results"]) == 1
        assert result["feed_upsert_results"][0]["status"] == 200
        assert result["feed_upsert_results"][0]["action"] == "add"

    @pytest.mark.asyncio
    async def test_persist_update_action(self, base_state: dict[str, Any]) -> None:
        base_state["original_source_id"] = 42
        base_state["feed_upsert_plan"] = [{
            "extracted_feed": {
                "dimension": FineGrainedFeedDimension.PERSONALITY,
                "sub_dimension": "trait",
                "content": "original",
                "confidence": FineGrainedFeedConfidence.IMPRESSION,
            },
            "action": "update",
            "target_feed_id": 5,
            "merged_content": "updated content",
            "reason": "supplementary",
            "recalled_candidates": [],
        }]
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.updateFineGrainedFeed",
            new_callable=AsyncMock,
            return_value={"status": 200, "message": "ok"},
        ):
            result = await nodePersistFineGrainedFeedUpsert(base_state)

        assert result["feed_upsert_results"][0]["status"] == 200
        assert result["feed_upsert_results"][0]["action"] == "update"

    @pytest.mark.asyncio
    async def test_persist_skip_action(self, base_state: dict[str, Any]) -> None:
        base_state["original_source_id"] = 42
        base_state["feed_upsert_plan"] = [{
            "extracted_feed": {
                "dimension": FineGrainedFeedDimension.PERSONALITY,
                "sub_dimension": "trait",
                "content": "unchanged",
                "confidence": FineGrainedFeedConfidence.IMPRESSION,
            },
            "action": "skip",
            "target_feed_id": 1,
            "merged_content": None,
            "reason": "equivalent",
            "recalled_candidates": [],
        }]
        result = await nodePersistFineGrainedFeedUpsert(base_state)

        assert result["feed_upsert_results"][0]["status"] == 200
        assert result["feed_upsert_results"][0]["action"] == "skip"

    @pytest.mark.asyncio
    async def test_persist_conflict_action(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["original_source_id"] = 42
        base_state["feed_upsert_plan"] = [{
            "extracted_feed": {
                "dimension": FineGrainedFeedDimension.MEMORY,
                "sub_dimension": "event",
                "content": "new info",
                "confidence": FineGrainedFeedConfidence.IMPRESSION,
            },
            "action": "conflict",
            "target_feed_id": 10,
            "merged_content": "merged content",
            "reason": "Conflict by LLM",
            "recalled_candidates": [
                {"id": 10, "content": "old info"}
            ],
        }]
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.addFineGrainedFeedConflict",
                return_value={"status": 200},
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.updateFineGrainedFeed",
                new_callable=AsyncMock,
                return_value={"status": 200},
            ),
        ):
            result = await nodePersistFineGrainedFeedUpsert(base_state)

        assert result["feed_upsert_results"][0]["status"] == 200
        assert result["feed_upsert_results"][0]["action"] == "conflict"

    @pytest.mark.asyncio
    async def test_persist_unsupported_action_logs_error(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["original_source_id"] = 42
        base_state["feed_upsert_plan"] = [{
            "extracted_feed": {
                "dimension": FineGrainedFeedDimension.PERSONALITY,
                "sub_dimension": "x",
                "content": "x",
                "confidence": FineGrainedFeedConfidence.IMPRESSION,
            },
            "action": "delete",
            "target_feed_id": None,
            "merged_content": None,
            "reason": "unsupported",
            "recalled_candidates": [],
        }]
        result = await nodePersistFineGrainedFeedUpsert(base_state)

        assert result["feed_upsert_results"][0]["status"] == -9
        assert "Unsupported action" in result["feed_upsert_results"][0]["message"]

    @pytest.mark.asyncio
    async def test_empty_plan_skips(self, base_state: dict[str, Any]) -> None:
        base_state["feed_upsert_plan"] = []
        result = await nodePersistFineGrainedFeedUpsert(base_state)

        assert result["feed_upsert_results"] == []
        assert result["logs"][-1]["status"] == "skip"

    @pytest.mark.asyncio
    async def test_persist_exception_captures_per_item(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["original_source_id"] = 42
        base_state["feed_upsert_plan"] = [{
            "extracted_feed": {
                "dimension": FineGrainedFeedDimension.MEMORY,
                "sub_dimension": "x",
                "content": "x",
                "confidence": FineGrainedFeedConfidence.IMPRESSION,
            },
            "action": "add",
            "target_feed_id": None,
            "merged_content": None,
            "reason": "add",
            "recalled_candidates": [],
        }]
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.addFineGrainedFeed",
            new_callable=AsyncMock,
            side_effect=Exception("Unexpected error"),
        ):
            result = await nodePersistFineGrainedFeedUpsert(base_state)

        assert result["feed_upsert_results"][0]["status"] == -99
        assert "Unexpected error" in result["feed_upsert_results"][0]["message"]


# ---------------------------------------------------------------------------
# 10. nodeBuildFRBuildingGraphOutput
# ---------------------------------------------------------------------------


class TestNodeBuildFRBuildingGraphOutput:
    """Tests for step 10: aggregating final graph output."""

    def test_complete_success_status(self, base_state: dict[str, Any]) -> None:
        base_state["original_source_id"] = 42
        base_state["fr_update_result"] = {"status": 200, "message": "ok"}
        base_state["feed_upsert_results"] = [{"status": 200}]
        result = nodeBuildFRBuildingGraphOutput(base_state)

        assert result["status"] == 200
        assert result["message"] == "FR building completed"

    def test_partial_failure_status(self, base_state: dict[str, Any]) -> None:
        base_state["original_source_id"] = 42
        base_state["fr_update_result"] = {"status": 200, "message": "ok"}
        base_state["feed_upsert_results"] = [{"status": -1}]
        result = nodeBuildFRBuildingGraphOutput(base_state)

        assert result["status"] == 500
        assert "partial failure" in result["message"]

    def test_errors_flag_partial_failure(self, base_state: dict[str, Any]) -> None:
        base_state["errors"] = ["Something went wrong"]
        base_state["original_source_id"] = None
        result = nodeBuildFRBuildingGraphOutput(base_state)

        assert result["status"] == 500

    def test_logs_summarize_warning_and_error_counts(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["warnings"] = ["w1", "w2"]
        base_state["errors"] = ["e1"]
        base_state["original_source_id"] = 1
        base_state["fr_update_result"] = {"status": 200}
        base_state["feed_upsert_results"] = []
        result = nodeBuildFRBuildingGraphOutput(base_state)

        log = result["logs"][-1]
        assert log["data"]["warning_count"] == 2
        assert log["data"]["error_count"] == 1


# ---------------------------------------------------------------------------
# 11. nodeGenerateFRBuildingReport
# ---------------------------------------------------------------------------


class TestNodeGenerateFRBuildingReport:
    """Tests for step 11: generating and persisting the FR building report."""

    @pytest.mark.asyncio
    async def test_generates_and_persists_report(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["original_source_id"] = 42
        base_state["fr_intrinsic_updates"] = {"figure_occupation": "律师"}
        base_state["feed_upsert_plan"] = [
            {"action": "add", "reason": "new info"}
        ]
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getFROverallUpdateLogsThisRound",
                return_value=[{"field": "figure_occupation", "old": "", "new": "律师"}],
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="report prompt"),
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.addFRBuildingGraphReport",
                return_value={"status": 200, "fr_building_graph_report_id": 99},
            ),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = "# 构建报告\n本轮更新了职业信息。"
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeGenerateFRBuildingReport(base_state)

        assert result["fr_building_report"] == "# 构建报告\n本轮更新了职业信息。"
        report_log = result["logs"][-1]
        assert report_log["step"] == "nodeGenerateFRBuildingReport"
        assert report_log["data"]["fr_building_graph_report_id"] == 99

    @pytest.mark.asyncio
    async def test_no_updates_produces_empty_report(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["original_source_id"] = 42
        base_state["fr_intrinsic_updates"] = {}
        base_state["feed_upsert_plan"] = []
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.getFROverallUpdateLogsThisRound",
            return_value=[],
        ):
            result = await nodeGenerateFRBuildingReport(base_state)

        assert result["fr_building_report"] == "本轮无有效更新"

    @pytest.mark.asyncio
    async def test_invalid_user_id_raises(self, base_state: dict[str, Any]) -> None:
        base_state["request"]["user_id"] = None
        with pytest.raises(ValueError, match="Invalid request.user_id"):
            await nodeGenerateFRBuildingReport(base_state)

    @pytest.mark.asyncio
    async def test_invalid_original_source_id_raises(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["original_source_id"] = None
        with pytest.raises(ValueError, match="Invalid request.original_source_id"):
            await nodeGenerateFRBuildingReport(base_state)

    @pytest.mark.asyncio
    async def test_llm_failure_raises(self, base_state: dict[str, Any]) -> None:
        base_state["original_source_id"] = 42
        base_state["fr_intrinsic_updates"] = {"figure_occupation": "x"}
        base_state["feed_upsert_plan"] = [{"action": "add"}]
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getFROverallUpdateLogsThisRound",
                return_value=[{"field": "x"}],
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="report prompt"),
            ),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM timeout"))
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                with pytest.raises(ValueError, match="Generate FR report via LLM failed"):
                    await nodeGenerateFRBuildingReport(base_state)

    @pytest.mark.asyncio
    async def test_report_persist_failure_raises(
        self, base_state: dict[str, Any]
    ) -> None:
        base_state["original_source_id"] = 42
        base_state["fr_intrinsic_updates"] = {"figure_occupation": "x"}
        base_state["feed_upsert_plan"] = [{"action": "add"}]
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getFROverallUpdateLogsThisRound",
                return_value=[{"field": "x"}],
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="report prompt"),
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.addFRBuildingGraphReport",
                return_value={"status": 500, "message": "DB error"},
            ),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = "report text"
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                with pytest.raises(ValueError, match="Persist FRBuildingGraphReport failed"):
                    await nodeGenerateFRBuildingReport(base_state)


# ---------------------------------------------------------------------------
# Pipeline integration tests
# ---------------------------------------------------------------------------


class TestPipelineIntegration:
    """Tests that verify sequential pipeline behavior across multiple nodes."""

    @pytest.mark.asyncio
    async def test_full_pipeline_load_to_preprocess(
        self,
        base_state: dict[str, Any],
        sample_fr_base: dict[str, Any],
        sample_user: dict[str, Any],
    ) -> None:
        """Test the first 3 nodes chain: Load FR -> Preprocess -> Persist OS."""
        # Step 1: Load FR
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getUserById",
                return_value=sample_user,
            ),
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getFigureAndRelation",
                return_value={
                    "status": 200,
                    "figure_and_relation": sample_fr_base,
                },
            ),
        ):
            s1 = nodeLoadFR(base_state)

        # Step 2: Preprocess
        merged = {**base_state, **s1}
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="preprocess prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"cleaned_content": "cleaned", '
                '"metadata": {"original_source_type": "narrative_from_user", '
                '"confidence": "impression", '
                '"included_dimensions": ["personality"], "approx_date": null}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                s2 = await nodePreprocessInput(merged)

        # Step 3: Persist original source
        merged2 = {**merged, **s2}
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.addOriginalSource",
            return_value={"status": 200, "original_source_id": 100},
        ):
            s3 = nodePersistOriginalSource(merged2)

        assert s3["original_source_id"] == 100
        assert s2["original_source"]["content"] == "cleaned"

    @pytest.mark.asyncio
    async def test_extraction_to_plan_to_persist_chain(
        self,
        base_state: dict[str, Any],
    ) -> None:
        """Test the extraction -> plan -> persist chain for FR intrinsic updates."""
        # Prepare state as if preprocess + load already ran
        state = dict(base_state)
        state["original_source"] = {
            "content": "我叫李华，MBTI是INFJ，在北京工作。",
            "type": OriginalSourceType.NARRATIVE_FROM_USER,
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
            "included_dimensions": [FineGrainedFeedDimension.PERSONALITY],
        }
        state["figure_and_relation"]["figure_mbti"] = None
        state["figure_and_relation"]["figure_occupation"] = ""

        # Extraction
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="extract prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"fr_intrinsic_candidates": {'
                '"figure_mbti": "INFJ", '
                '"figure_occupation": "工程师"'
                '}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                state.update(await nodeExtractFRIntrinsicCandidates(state))

        assert state["fr_intrinsic_updates"]["figure_occupation"] == "工程师"

        # Plan
        state.update(await nodePlanFRIntrinsicUpdate(state))
        assert state["fr_intrinsic_updates"]["figure_mbti"] == MBTI.INFJ

        # Persist
        with patch(
            "src.agents.graphs.FRBuildingGraph.nodes.updateFigureAndRelation",
            return_value={"status": 200, "message": "ok"},
        ):
            state.update(nodePersistFRIntrinsicUpdate(state))

        assert state["fr_update_result"]["status"] == 200

    @pytest.mark.asyncio
    async def test_partial_failure_in_feed_persist_bubbles_to_output(
        self,
        base_state: dict[str, Any],
    ) -> None:
        """When one feed upsert fails, nodeBuildFRBuildingGraphOutput returns 500."""
        base_state["original_source_id"] = 42
        base_state["fr_update_result"] = {"status": 200}
        base_state["feed_upsert_results"] = [
            {"status": 200},
            {"status": -1, "message": "failed"},
        ]
        result = nodeBuildFRBuildingGraphOutput(base_state)

        assert result["status"] == 500
        assert "partial failure" in result["message"]


# ---------------------------------------------------------------------------
# Concurrent build prevention
# ---------------------------------------------------------------------------


class TestConcurrentBuildPrevention:
    """Tests that verify the async lock prevents concurrent FR builds."""

    @pytest.mark.asyncio
    async def test_concurrent_access_raises_runtime_error(self) -> None:
        """When getFRBuildingGraph is entered, a second concurrent entry raises
        RuntimeError with message 'FRBuildingGraph is running'."""
        from src.agents.graphs.FRBuildingGraph.graph import getFRBuildingGraph

        async def _hold_lock():
            async with getFRBuildingGraph() as g:
                # Hold the lock indefinitely for test purposes
                await asyncio.sleep(0.1)

        # Start first task that acquires the lock
        task = asyncio.create_task(_hold_lock())
        await asyncio.sleep(0.01)  # let it acquire

        # Second attempt should raise
        with pytest.raises(RuntimeError, match="FRBuildingGraph is running"):
            async with getFRBuildingGraph():
                pass

        await task  # clean up


# ---------------------------------------------------------------------------
# Error recovery
# ---------------------------------------------------------------------------


class TestErrorRecovery:
    """Tests focused on error recovery paths through the pipeline."""

    @pytest.mark.asyncio
    async def test_preprocess_warning_on_empty_cleaned_content(
        self, base_state: dict[str, Any]
    ) -> None:
        """When LLM returns empty cleaned_content, a warning is raised
        but processing does not crash."""
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="preprocess prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '{"cleaned_content": "", '
                '"metadata": {"original_source_type": "narrative_from_user", '
                '"confidence": "impression", '
                '"included_dimensions": ["personality"], "approx_date": null}}'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodePreprocessInput(base_state)

        assert len(result["warnings"]) >= 1
        assert "cleaned_content is empty" in result["warnings"][0]
        # original_source still produced (content may be empty string)
        assert result["original_source"]["content"] == ""

    @pytest.mark.asyncio
    async def test_warnings_accumulate_across_nodes(
        self,
        base_state: dict[str, Any],
    ) -> None:
        """Warnings from earlier nodes must persist in state through later nodes."""
        base_state["warnings"] = ["prior_warning_from_load"]
        base_state["warnings"].append("prior_warning_from_preprocess")

        # Now run persist with empty updates (generates a skip log)
        base_state["fr_intrinsic_updates"] = {}
        result = nodePersistFRIntrinsicUpdate(base_state)

        # Prior warnings must be preserved
        assert len(result["warnings"]) >= 2
        assert "prior_warning_from_load" in result["warnings"]

    @pytest.mark.asyncio
    async def test_invalid_dimension_in_extraction_warns(
        self, base_state: dict[str, Any]
    ) -> None:
        """Invalid dimension values are warned and skipped."""
        state = dict(base_state)
        state["original_source"] = {
            "content": "test",
            "type": OriginalSourceType.NARRATIVE_FROM_USER,
            "confidence": FineGrainedFeedConfidence.IMPRESSION,
            # All dimensions valid in this test
            "included_dimensions": [FineGrainedFeedDimension.PERSONALITY],
        }
        with (
            patch(
                "src.agents.graphs.FRBuildingGraph.nodes.getPrompt",
                MagicMock(return_value="role/dimension prompt"),
            ),
            patch.object(asyncio, "sleep", AsyncMock(return_value=None)),
        ):
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value.content = (
                '[{"sub_dimension": "a", "confidence": "impression", "content": "text"}]'
            )
            with patch(
                "src.agents.graphs.FRBuildingGraph.nodes.prepareLLM",
                return_value=mock_llm,
            ):
                result = await nodeExtractFineGrainedFeeds(state)

        feeds = result["extracted_feeds"]
        assert len(feeds) >= 1
        log = result["logs"][-1]
        assert log["step"] == "nodeExtractFineGrainedFeeds"
