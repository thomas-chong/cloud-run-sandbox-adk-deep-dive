from sandbox_analyst.agent import root_agent
from sandbox_analyst.executor import AuditedCloudRunSandboxCodeExecutor


def test_agent_uses_gemini_35_and_sandbox_capabilities() -> None:
    assert root_agent.name == "sandbox_pr_reviewer"
    assert root_agent.model == "gemini-3.5-flash"
    assert isinstance(root_agent.code_executor, AuditedCloudRunSandboxCodeExecutor)
    assert root_agent.code_executor.allow_egress is False
    assert root_agent.code_executor.timeout_seconds == 20
    tool_names = {tool.__name__ for tool in root_agent.tools}
    assert "start_review_workspace" in tool_names
    assert "inspect_security_boundaries" in tool_names
    assert "benchmark_sandbox_startup" in tool_names
    assert "estimate_monthly_cost" in tool_names
