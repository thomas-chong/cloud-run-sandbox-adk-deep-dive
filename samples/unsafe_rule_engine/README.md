# Deliberately unsafe rule engine

This fixture is not production code. Its use of `eval` creates a realistic repair task
for the sandboxed PR-review agent. Tests and the boundary probe must only run inside a
Cloud Run sandbox.
