from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.code_agent import code_node
from app.agents.deploy_agent import deploy_node
from app.agents.plan_agent import plan_node
from app.agents.security_agent import security_node
from app.agents.state import AgentState
from app.agents.test_agent import test_node


def _after_code(state: AgentState) -> str:
    """Route after the Code Agent.

    - build succeeds            → test
    - build fails, error set     → end (parse/sandbox failure or retries exhausted)
    - build fails, retry pending → back to code (with build_error as context)
    """
    if state.get("build_success"):
        return "test"
    if state.get("error"):
        return END
    return "code"


def _after_test(state: AgentState) -> str:
    """Route after the Test Agent.

    - tests pass               → security
    - tests fail, error set     → end (parse/sandbox failure or retries exhausted)
    - tests fail, retry pending → back to code (with test_failures as context)

    The Test Agent increments `retry_count` and sets `error` itself, mirroring the
    Code Agent — so this routing is symmetric with `_after_code`.
    """
    if state.get("tests_passed"):
        return "security"
    if state.get("error"):
        return END
    return "code"


def _after_security(state: AgentState) -> str:
    """Route after the Security Agent: deploy only if cleared."""
    if state.get("security_cleared"):
        return "deploy"
    return END


def build_graph() -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    graph = StateGraph(AgentState)

    graph.add_node("plan", plan_node)
    graph.add_node("code", code_node)
    graph.add_node("test", test_node)
    graph.add_node("security", security_node)
    graph.add_node("deploy", deploy_node)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "code")
    graph.add_conditional_edges("code", _after_code, ["code", "test", END])
    graph.add_conditional_edges("test", _after_test, ["code", "security", END])
    graph.add_conditional_edges("security", _after_security, ["deploy", END])
    graph.add_edge("deploy", END)

    return graph.compile()


# Compiled once at import; reused across requests.
pipeline = build_graph()
