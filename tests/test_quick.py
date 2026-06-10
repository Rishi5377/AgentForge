import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', '.env')))

from workflows.pipeline import create_pipeline, GraphState

async def test_app():
    pipeline = create_pipeline()
    session_id = "test_quick_local"
    state = GraphState({
        "user_prompt": "Create a simple hello world landing page. No backend needed.",
        "session_id": session_id,
        "workspace_dir": os.path.abspath(os.path.join("backend", "workspace", session_id)),
        "messages": [],
        "plan": {},
        "execution_order": [],
        "current_step_idx": 0,
        "validation_errors": {},
        "retry_counts": {},
        "next_worker": "",
        "last_active_agent": "",
        "qa_retry_count": 0
    })
    
    print(f"\n==== Starting test: {session_id} ====")
    
    try:
        async for event in pipeline.astream(state):
            for k, v in event.items():
                print(f"-> Node {k} finished.")
                if "validation_errors" in v and v["validation_errors"].get("qa"):
                    print(f"QA Error: {v['validation_errors']['qa']}")
    except Exception as e:
        print(f"Pipeline error: {e}")
        
    print(f"==== Finished test: {session_id} ====\n")

if __name__ == "__main__":
    asyncio.run(test_app())
