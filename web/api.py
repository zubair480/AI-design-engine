"""
FastAPI backend with WebSocket support for real-time agent updates.

Serves both the REST API and the React frontend static files.
Deployed as a Modal ASGI app.
"""

import json
import asyncio
import os
from typing import Any

import modal
from config import app, web_image, results_vol


@app.function(
    image=web_image,
    volumes={"/results": results_vol},
    timeout=900,
)
@modal.asgi_app()
def web():
    """Create and return the FastAPI application."""
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from pydantic import BaseModel

    web_app = FastAPI(
        title="AI Decision Engine",
        description="Autonomous multi-agent business analysis platform",
        version="1.0.0",
    )

    # CORS for local React dev server
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Request / Response models ----

    class AnalyzeRequest(BaseModel):
        prompt: str

    class FollowupRequest(BaseModel):
        session_id: str
        prompt: str
        override_params: dict[str, Any] | None = None

    class AnalyzeResponse(BaseModel):
        session_id: str
        message: str

    # ---- API Endpoints ----

    @web_app.post("/api/analyze")
    async def analyze(request: Request):
        """
        Launch the full analysis pipeline.
        Returns immediately with a session_id for tracking.
        """
        import uuid
        from agents.orchestrator import run_pipeline

        prompt: str | None = None

        try:
            body = await request.body()
            payload = json.loads(body)
            if isinstance(payload, dict):
                value = payload.get("prompt")
                if isinstance(value, str) and value.strip():
                    prompt = value.strip()
            elif isinstance(payload, str) and payload.strip():
                prompt = payload.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")

        if not prompt:
            raise HTTPException(status_code=422, detail="Missing 'prompt' string in request body")

        session_id = uuid.uuid4().hex[:12]

        # Spawn the pipeline asynchronously (fire-and-forget)
        run_pipeline.spawn(prompt, session_id)

        return AnalyzeResponse(
            session_id=session_id,
            message="Pipeline started. Connect to WebSocket for real-time updates.",
        )

    @web_app.get("/api/status/{session_id}")
    async def get_status(session_id: str):
        """Poll current pipeline status for a session."""
        from memory.store import get_status, load

        status = get_status(session_id)
        return {
            "session_id": session_id,
            "status": status,
        }

    @web_app.get("/api/results/{session_id}")
    async def get_results(session_id: str):
        """Get full final results for a completed session."""
        from memory.store import load

        final = load(session_id, "final_output")
        if final is None:
            # Try to get partial results
            evaluation = load(session_id, "final")
            if evaluation:
                return {"session_id": session_id, "status": "complete", "data": evaluation}
            raise HTTPException(status_code=404, detail="Results not ready yet")

        return {"session_id": session_id, "status": "complete", "data": final}

    @web_app.post("/api/followup")
    async def followup(request: Request):
        """
        Run a follow-up query on an existing session.
        Reuses prior research, re-runs simulation with modified params.
        """
        from agents.orchestrator import run_followup

        session_id: str | None = None
        prompt: str | None = None
        override_params: dict[str, Any] | None = None

        try:
            payload = await request.json()
        except Exception:
            payload = {}

        if isinstance(payload, dict):
            sid_value = payload.get("session_id")
            prompt_value = payload.get("prompt")
            override_value = payload.get("override_params")

            if isinstance(sid_value, str):
                session_id = sid_value.strip()
            if isinstance(prompt_value, str):
                prompt = prompt_value.strip()
            if isinstance(override_value, dict):
                override_params = override_value

        if not session_id or not prompt:
            raise HTTPException(status_code=422, detail="Missing 'session_id' or 'prompt' in request body")

        # override_regions can be passed as a list of "City, ST" strings
        override_regions = None
        if isinstance(payload, dict) and isinstance(payload.get("override_regions"), list):
            override_regions = payload["override_regions"]

        run_followup.spawn(
            session_id,
            prompt,
            override_regions,
        )

        return {
            "session_id": session_id,
            "message": "Follow-up analysis started.",
        }

    @web_app.get("/api/session/{session_id}/context")
    async def get_context(session_id: str):
        """Get all stored data for a session (for debugging / transparency)."""
        from memory.store import get_session_context
        return get_session_context(session_id)

    # ---- WebSocket for real-time events ----

    @web_app.websocket("/api/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        """
        Stream real-time agent events to the frontend.

        Events include:
        - plan_complete
        - research_started / research_complete
        - simulation_started / simulation_progress / simulation_complete
        - evaluation_started / evaluation_complete
        - pipeline_complete
        """
        await websocket.accept()

        try:
            while True:
                # Poll the event queue for this session
                from memory.store import poll_events, get_status

                events = poll_events(session_id, timeout=1.0)
                for event in events:
                    await websocket.send_json(event)

                # Check if pipeline is complete
                status = get_status(session_id)
                if status.get("phase") == "complete":
                    # Send final status and close
                    await websocket.send_json({
                        "event": "done",
                        "status": status,
                    })
                    break

                # Small delay to avoid tight loop
                await asyncio.sleep(0.5)

        except WebSocketDisconnect:
            pass
        except Exception as e:
            try:
                await websocket.send_json({"event": "error", "message": str(e)})
            except Exception:
                pass

    # ---- Health check ----

    @web_app.get("/api/health")
    async def health():
        return {"status": "ok", "service": "ai-decision-engine"}

    # ---- Serve React frontend (static files) ----
    # Built React app is at /assets/frontend/dist
    frontend_dir = "/assets/frontend/dist"
    if os.path.isdir(frontend_dir):
        @web_app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            """Serve the React SPA for all non-API routes."""
            file_path = os.path.join(frontend_dir, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(frontend_dir, "index.html"))
    else:
        @web_app.get("/{full_path:path}")
        async def serve_fallback(full_path: str):
            """Fallback when frontend not available."""
            return {"message": "Frontend not available in this deployment"}


    return web_app
