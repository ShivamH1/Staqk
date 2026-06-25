from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # Input
    project_id: str
    user_message: str
    tech_stack: dict[str, Any]
    existing_file_tree: dict[str, str]

    # Plan Agent output
    plan: dict[str, Any]

    # Code Agent output
    file_tree: dict[str, str]
    build_success: bool
    build_error: str | None  # truncated build log, fed back on retry

    # Test Agent output
    test_results: list[dict[str, Any]]
    tests_passed: bool

    # Security Agent output
    security_findings: list[dict[str, Any]]
    security_cleared: bool

    # Deploy Agent output
    deployment_url: str | None

    # Control
    error: str | None
    retry_count: int


# Max times the Code Agent re-runs when build/tests fail
MAX_CODE_RETRIES = 2
