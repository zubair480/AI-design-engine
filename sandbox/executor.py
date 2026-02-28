"""
Sandbox Executor — Securely runs LLM-generated Python code in Modal sandboxes.

Used by agents when they need to dynamically generate and execute analysis code,
proving the agent → tool → execution loop.
"""

from __future__ import annotations

import modal
from config import app, sim_image, results_vol


@app.function(image=sim_image, timeout=120)
def execute_code(
    code: str,
    timeout: int = 60,
    session_id: str | None = None,
) -> dict:
    """
    Execute arbitrary Python code in a sandboxed Modal container.

    Args:
        code: Python source code to execute.
        timeout: Max execution time in seconds.
        session_id: Optional session for logging.

    Returns:
        Dict with stdout, stderr, exit_code, and execution_time.
    """
    import time

    start = time.time()

    sb = modal.Sandbox.create(
        image=sim_image,
        timeout=timeout,
        app=app,
    )

    try:
        # Write code to a temp file and execute
        process = sb.exec("python", "-c", code, timeout=timeout)
        stdout = process.stdout.read()
        stderr = process.stderr.read()
        process.wait()
        exit_code = process.returncode
    except Exception as e:
        stdout = ""
        stderr = str(e)
        exit_code = -1
    finally:
        sb.terminate()

    elapsed = round(time.time() - start, 3)

    result = {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "execution_time_seconds": elapsed,
    }

    # Log to memory if session provided
    if session_id:
        from memory.store import emit_event
        emit_event(session_id, {
            "event": "sandbox_execution",
            "code_length": len(code),
            "exit_code": exit_code,
            "execution_time": elapsed,
        })

    return result


@app.function(image=sim_image, timeout=120)
def execute_analysis(
    session_id: str,
    analysis_description: str,
) -> dict:
    """
    Use LLM to generate analysis code, then execute it in a sandbox.

    This demonstrates the full agent → code generation → execution → result loop.

    Args:
        session_id: Session identifier.
        analysis_description: What kind of analysis to run.

    Returns:
        Dict with generated code, execution result, and parsed output.
    """
    from llm.client import call_llm
    from memory.store import load, emit_event

    # Get simulation data for context
    sim_data = load(session_id, "simulation", {})
    profit_stats = sim_data.get("profit", {})

    # Ask LLM to generate analysis code
    code = call_llm(
        prompt=f"""Write a Python script to perform this analysis: {analysis_description}

Use these profit statistics:
- Mean: {profit_stats.get('mean', 0)}
- Std: {profit_stats.get('std', 0)}
- P10: {profit_stats.get('p10', 0)}
- P90: {profit_stats.get('p90', 0)}

The script should:
1. Import only numpy and math (already installed)
2. Print results as a single JSON object to stdout
3. Be self-contained (no file I/O)
4. Be under 50 lines

Output ONLY the Python code. No markdown, no explanation.""",
        system_prompt="You are a Python code generator. Output only executable Python code.",
        temperature=0.1,
    )

    # Clean up code (strip markdown fences if present)
    import re
    code = code.strip()
    fence_match = re.search(r"```(?:python)?\s*\n?(.*?)```", code, re.DOTALL)
    if fence_match:
        code = fence_match.group(1).strip()

    emit_event(session_id, {
        "event": "code_generated",
        "description": analysis_description,
        "code_length": len(code),
    })

    # Execute in sandbox
    result = execute_code.remote(code, timeout=30, session_id=session_id)

    # Try to parse stdout as JSON
    parsed_output = None
    if result["exit_code"] == 0 and result["stdout"]:
        try:
            import json
            parsed_output = json.loads(result["stdout"])
        except json.JSONDecodeError:
            parsed_output = {"raw_output": result["stdout"]}

    return {
        "code": code,
        "execution": result,
        "parsed_output": parsed_output,
        "analysis_description": analysis_description,
    }
