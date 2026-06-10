import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure backend modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# Load env variables
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', '.env')))

from workflows.pipeline import create_pipeline, GraphState

async def test_app(prompt: str, session_id: str):
    pipeline = create_pipeline()
    state = GraphState({
        "user_prompt": prompt,
        "session_id": session_id,
        "workspace_dir": os.path.abspath(f"workspace_{session_id}"),
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
    print(f"Prompt: {prompt}")
    
    try:
        async for event in pipeline.astream(state):
            for k, v in event.items():
                if k == "supervisor" and "plan" in v:
                    print(f"-> Supervisor selected template: {v['plan'].get('project_template')}")
                else:
                    print(f"-> Node {k} finished.")
                
                if "validation_errors" in v and v["validation_errors"].get("qa"):
                    print(f"QA Error: {v['validation_errors']['qa']}")
    except Exception as e:
        print(f"Pipeline error: {e}")
        
    print(f"==== Finished test: {session_id} ====\n")

async def main():
    print("Testing SvelteKit Routing...")
    prompt1 = """Build a highly optimized, compiler-driven web app for managing a personal book collection.
Features:
- Add, edit, and delete books.
- Track reading status (Not Started, Reading, Completed).
- Search and filter books.
- Sort by title, author, or date added.
- Reading statistics dashboard.
- Local storage persistence.
Technical Requirements:
- Responsive design.
- Clean modern UI.
- Component-based architecture."""
    await test_app(prompt1, "library_manager_test")
    
    print("Testing Vue Routing...")
    prompt2 = """Build a lightweight, performant single-page application for tracking student grades.
Features:
- Add students and subjects.
- Record marks and grades.
- Calculate averages automatically.
- Search and filter students.
- Performance dashboard.
- Export report as CSV.
Technical Requirements:
- Responsive layout.
- Data persistence using local storage."""
    await test_app(prompt2, "grade_tracker_test")
    
    print("Testing React Routing...")
    prompt3 = """Build a complex internal tool and dashboard for inventory management.
Features:
- Add, edit, and remove products.
- Track stock quantities.
- Low-stock alerts.
- Product categories.
- Search and filtering.
- Inventory statistics dashboard.
Technical Requirements:
- Responsive UI.
- Persistent local storage."""
    await test_app(prompt3, "inventory_system_test")
    
    print("Testing NextJS Routing...")
    prompt4 = """Build a public-facing daily journal and public blog application where SEO is critical.
Features:
- Create, edit, and delete journal entries.
- Search previous entries.
- Mood tracking.
- Calendar view.
- Writing statistics.
- Auto-save functionality.
Technical Requirements:
- Responsive design.
- Local data persistence."""
    await test_app(prompt4, "journal_app_test")

if __name__ == "__main__":
    asyncio.run(main())
