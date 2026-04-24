# app/graph/builder.py
"""
Assembles and compiles the SkillGapAnalyzer LangGraph pipeline.

Concept recap before reading:

  add_edge(A, B)
    → fixed: after A always goes to B.

  add_edge(A, [B, C])
    → fan-out: after A, run B and C IN PARALLEL (same superstep).
      Both get the same state snapshot. Their return dicts are merged
      back using reducers. No explicit "fan-in" call needed — LangGraph
      automatically waits for all superstep nodes to finish.

  add_conditional_edges(A, fn, {key: node, ...})
    → fn(state) returns a key string. LangGraph looks up the matching
      node in the dict and routes there.
      The dict is your safety net: LangGraph validates that every string
      fn() could return maps to a real node. Typos = compile error.

  Compilation: builder.compile() validates connectivity (no orphan nodes,
  no unreachable nodes) and returns an executable CompiledStateGraph.
  You cannot call .invoke() on a StateGraph — only on a CompiledStateGraph.
"""

from langgraph.graph import StateGraph, START, END

from app.graph.state import SkillGapState
from app.graph.nodes.cv_parser_node import cv_parser_agent
from app.graph.nodes.jd_analyst_node import jd_analyst_agent
from app.graph.nodes.gap_analyst_node import gap_analyst_agent
from app.graph.nodes.coach_node import coach_agent
from app.graph.nodes.error_node import error_node
from app.graph.edges.routing import route_after_jd_gate, route_after_coach
from app.core.logger import logger


def build_graph() -> StateGraph:
    """
    Constructs the graph builder (not yet compiled).
    Separated from compile_graph() so tests can inspect the builder
    without needing a checkpointer.
    """
    builder = StateGraph(SkillGapState)

    # ── 1. Register nodes ──────────────────────────────────────────────────
    # add_node(name, function)
    # 'name' is the string used in all edge declarations.
    # 'function' is the node callable: (state) -> dict
    builder.add_node("cv_parser_agent",   cv_parser_agent)
    builder.add_node("jd_analyst_agent",  jd_analyst_agent)
    builder.add_node("gap_analyst_agent", gap_analyst_agent)
    builder.add_node("coach_agent",       coach_agent)
    builder.add_node("error_node",        error_node)

    # ── 2. Entry: START → parallel fan-out ────────────────────────────────
    # Passing a LIST to add_edge creates a fan-out.
    # cv_parser_agent and jd_analyst_agent run simultaneously.
    # They write to different state keys so no reducer conflict.
    builder.add_edge(START, "cv_parser_agent")
    builder.add_edge(START, "jd_analyst_agent")

    # ── 3. Fan-in: both parallel nodes → gap_analyst_agent ────────────────
    # LangGraph automatically waits for ALL nodes from the previous superstep
    # before advancing. When both cv_parser_agent AND jd_analyst_agent have
    # written their results, the next node becomes eligible to run.
    #
    # But we don't go straight to gap_analyst — we go through the quality gate.
    # The "gate" is not a real node; it's modelled as a conditional edge
    # fired after jd_analyst_agent finishes.
    #
    # Why after jd_analyst specifically (not cv_parser)?
    # Because the malformed flag lives on JDRequirements. cv_parser doesn't
    # know if the JD is garbage — it only parsed the CV.
    # We wait for BOTH to finish, but the routing decision reads JD state.
    #
    # Implementation: add edges from both parallel nodes into a fan-in target.
    # The conditional edge on jd_analyst_agent fires AFTER both are done
    # because LangGraph superstep semantics: all nodes in a superstep
    # complete before ANY outgoing edges fire.
    builder.add_edge("cv_parser_agent", "jd_analyst_agent")  # fan-in sync point

    # ── 4. Conditional edge: jd quality gate ──────────────────────────────
    # route_after_jd_gate(state) returns "gap_analyst_agent" or "error_node"
    # The dict maps those return strings to node names (same here, but the
    # dict is where you'd rename if node name differs from return string).
    builder.add_conditional_edges(
        "jd_analyst_agent",
        route_after_jd_gate,
        {
            "gap_analyst_agent": "gap_analyst_agent",
            "error_node":        "error_node",
        }
    )

    # ── 5. Gap analysis → coach (sequential, fixed) ───────────────────────
    builder.add_edge("gap_analyst_agent", "coach_agent")

    # ── 6. Conditional edge: coach loop-or-end ────────────────────────────
    # route_after_coach returns "gap_analyst_agent" (retry) or "__end__"
    # "__end__" is LangGraph's built-in END sentinel as a string.
    builder.add_conditional_edges(
        "coach_agent",
        route_after_coach,
        {
            "gap_analyst_agent": "gap_analyst_agent",
            "__end__":           END,
        }
    )

    # ── 7. Error node → END (terminal, no conditional needed) ─────────────
    builder.add_edge("error_node", END)

    logger.info("[builder] Graph structure assembled. Nodes=%s", list(builder.nodes))
    return builder


def compile_graph():
    """
    Compiles the graph into an executable CompiledStateGraph.

    compile() does three things:
    1. Validates graph structure (orphan nodes, unreachable edges)
    2. Injects the checkpointer (None here — add InMemorySaver later for
       conversation memory / human-in-the-loop)
    3. Returns a CompiledStateGraph that exposes .invoke(), .stream(),
       .ainvoke(), .astream()
    """
    builder = build_graph()
    graph = builder.compile()
    logger.info("[builder] Graph compiled successfully.")
    return graph


# Module-level singleton — import this in routes.py
skill_gap_graph = compile_graph()