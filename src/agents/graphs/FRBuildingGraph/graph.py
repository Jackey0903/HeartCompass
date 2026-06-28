import asyncio
import logging
from contextlib import asynccontextmanager

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from src.agents.graphs.FRBuildingGraph.state import (
    FRBuildingGraphInput,
    FRBuildingGraphOutput,
    FRBuildingGraphState,
)
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

logger = logging.getLogger(__name__)

_fr_building_graph_lock = asyncio.Lock()
_fr_building_graph_instance: CompiledStateGraph | None = None


def buildFRBuildingGraph() -> CompiledStateGraph:
    graph = StateGraph(
        state_schema=FRBuildingGraphState,
        input_schema=FRBuildingGraphInput,
        output_schema=FRBuildingGraphOutput,
    )

    graph.add_node("nodeLoadFR", nodeLoadFR)
    graph.add_node("nodePreprocessInput", nodePreprocessInput)
    graph.add_node("nodePersistOriginalSource", nodePersistOriginalSource)
    graph.add_node("nodeExtractFRIntrinsicCandidates", nodeExtractFRIntrinsicCandidates)
    graph.add_node("nodePlanFRIntrinsicUpdate", nodePlanFRIntrinsicUpdate)
    graph.add_node("nodePersistFRIntrinsicUpdate", nodePersistFRIntrinsicUpdate)
    graph.add_node("nodeExtractFineGrainedFeeds", nodeExtractFineGrainedFeeds)
    graph.add_node("nodePlanFineGrainedFeedUpsert", nodePlanFineGrainedFeedUpsert)
    graph.add_node("nodePersistFineGrainedFeedUpsert", nodePersistFineGrainedFeedUpsert)
    graph.add_node("nodeBuildFRBuildingGraphOutput", nodeBuildFRBuildingGraphOutput)
    graph.add_node("nodeGenerateFRBuildingReport", nodeGenerateFRBuildingReport)

    graph.add_edge(START, "nodeLoadFR")
    graph.add_edge("nodeLoadFR", "nodePreprocessInput")
    graph.add_edge("nodePreprocessInput", "nodePersistOriginalSource")
    graph.add_edge("nodePersistOriginalSource", "nodeExtractFRIntrinsicCandidates")
    graph.add_edge("nodeExtractFRIntrinsicCandidates", "nodePlanFRIntrinsicUpdate")
    graph.add_edge("nodePlanFRIntrinsicUpdate", "nodePersistFRIntrinsicUpdate")
    graph.add_edge("nodePersistFRIntrinsicUpdate", "nodeExtractFineGrainedFeeds")
    graph.add_edge("nodeExtractFineGrainedFeeds", "nodePlanFineGrainedFeedUpsert")
    graph.add_edge("nodePlanFineGrainedFeedUpsert", "nodePersistFineGrainedFeedUpsert")
    graph.add_edge("nodePersistFineGrainedFeedUpsert", "nodeBuildFRBuildingGraphOutput")
    graph.add_edge("nodeBuildFRBuildingGraphOutput", "nodeGenerateFRBuildingReport")
    graph.add_edge("nodeGenerateFRBuildingReport", END)

    return graph.compile()


@asynccontextmanager
async def getFRBuildingGraph():
    global _fr_building_graph_instance

    if _fr_building_graph_lock.locked():
        raise RuntimeError("FRBuildingGraph is running")

    async with _fr_building_graph_lock:
        if _fr_building_graph_instance is None:
            _fr_building_graph_instance = buildFRBuildingGraph()
        yield _fr_building_graph_instance
