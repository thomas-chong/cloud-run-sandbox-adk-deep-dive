from sandbox_analyst.policy import ExecutionPolicy, evaluate_python


def test_allows_small_standard_library_program() -> None:
    code = "import statistics\nprint(statistics.mean([1, 2, 3]))"
    decision = evaluate_python(code, ExecutionPolicy())
    assert decision.allowed
    assert decision.reason == "allowed"


def test_blocks_configured_module() -> None:
    decision = evaluate_python("import subprocess\nprint('no')", ExecutionPolicy())
    assert not decision.allowed
    assert decision.reason == "blocked import: subprocess"


def test_blocks_dynamic_execution() -> None:
    decision = evaluate_python("eval('1 + 1')", ExecutionPolicy())
    assert not decision.allowed
    assert decision.reason == "blocked call: eval"


def test_rejects_invalid_python() -> None:
    decision = evaluate_python("if:", ExecutionPolicy())
    assert not decision.allowed
    assert "syntax error" in decision.reason


def test_enforces_utf8_byte_limit() -> None:
    policy = ExecutionPolicy(max_code_bytes=5)
    decision = evaluate_python("print('é')", policy)
    assert not decision.allowed
    assert "limit is 5" in decision.reason
