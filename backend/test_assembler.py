import sys
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from agents.assembler import AssemblerAgent

dummy_state = {
    "project_template": "react-tailwind",
    "files": {
        "src/App.jsx": "import React from 'react';\nfunction App() { return <div className='bg-green-500 text-white p-10 text-4xl font-bold'>AgentForge Counter Test</div>; }\nexport default App;",
        "src/main.jsx": "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App.jsx';\nimport './index.css';\n\nReactDOM.createRoot(document.getElementById('root')).render(<App />);\n",
        "src/index.css": "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n",
        "index.html": "<!DOCTYPE html><html lang='en'><head><title>Test App</title></head><body><div id='root'></div><script type='module' src='/src/main.jsx'></script></body></html>"
    }
}

async def main():
    print("Testing assembler...")
    agent = AssemblerAgent()
    # It expects: db_code, backend_code, frontend_code, plan_json, session_id
    frontend_code = str(dummy_state["files"])
    plan_json = '{"template": "react-tailwind"}'
    new_state = await agent.execute("", "", frontend_code, plan_json, "test_session")
    print("Assembler finished.")

if __name__ == "__main__":
    asyncio.run(main())
