import asyncio
import os
import sys
import uuid
from dotenv import load_dotenv

load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from workflows.pipeline import create_pipeline

async def main():
    print("Compiling pipeline...")
    pipeline = create_pipeline()
    
    session_id = "test_lms_" + str(uuid.uuid4())[:8]
    workspace_dir = os.path.join(os.path.dirname(__file__), "workspace", f"app_{session_id}")
    
    print(f"Workspace will be: {workspace_dir}")
    
    initial_state = {
        "user_prompt": """# Learning Management System

Build a full-stack LMS where instructors can create courses and students can enroll.

Features:
- User authentication and role management (Admin, Instructor, Student)
- Course creation and management
- Video lessons and downloadable resources
- Progress tracking
- Quizzes and assignments
- Student dashboard
- Course ratings and reviews
- Certificate generation upon completion

Technical Requirements:
- Responsive UI
- REST API
- Database persistence
- File uploads
- JWT authentication
- Use Next.js App router and Prisma""",
        "session_id": session_id,
        "workspace_dir": workspace_dir,
        "messages": [],
        "plan": {},
        "execution_order": [],
        "current_step_idx": 0,
        "validation_errors": {},
        "retry_counts": {},
        "last_active_agent": ""
    }
    
    config = {"configurable": {"workspace_dir": workspace_dir}}
    
    print("Running LMS generation...")
    try:
        final_state = await pipeline.ainvoke(initial_state, config=config)
        print("Generation complete!")
        print("Execution order was:", final_state.get("execution_order"))
        print("Checking workspace dir...")
        if os.path.exists(workspace_dir):
            files = os.listdir(workspace_dir)
            print(f"Workspace contains {len(files)} items: {files}")
        else:
            print("Workspace dir was not created!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
