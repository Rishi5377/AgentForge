import asyncio
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from workflows.pipeline import create_pipeline

async def main():
    print("Compiling pipeline...")
    pipeline = create_pipeline()
    
    print("Running generation...")
    initial_state = {
        "user_prompt": "Create a simple React counter app using Tailwind CSS with a big centered number and increment/decrement buttons.",
        "project_template": "react-tailwind"
    }
    
    final_state = await pipeline.ainvoke(initial_state)
    print("Generation complete!")
    print("Final State Keys:", final_state.keys())
    
    if "files" in final_state:
        print("Generated files:")
        for k in final_state["files"].keys():
            print(f"- {k}")

if __name__ == "__main__":
    asyncio.run(main())
