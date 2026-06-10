import asyncio
import websockets
import json

TEST_CASES = [
    {"name": "Beginner Test #1: Simple To-Do List", "prompt": """Build a simple To-Do List web application. Features: Add a task, View all tasks, Mark task as completed, Delete task, Display total tasks, Responsive design. Generate HTML, CSS, JavaScript. No database required. Store tasks in Local Storage."""},
    {"name": "Beginner Test #2: Student Registration Form", "prompt": """Build a Student Registration System. Features: Student Name, Roll Number, Branch, Email, Phone Number, Submit button, Display registered students in a table, Edit student details, Delete student details. Use HTML, CSS, JavaScript. Store data in Local Storage."""},
    {"name": "Beginner Test #3: Calculator", "prompt": """Build a Calculator application. Features: Addition, Subtraction, Multiplication, Division, Clear button, Responsive UI. Generate complete source code using HTML, CSS, and JavaScript."""},
    {"name": "Beginner Test #4: Expense Tracker", "prompt": """Build a simple Expense Tracker. Features: Add expense, Expense amount, Expense category, Display all expenses, Show total expenses, Delete expense. Use Local Storage for data persistence."""},
    {"name": "Beginner Test #5: Weather App", "prompt": """Build a Weather Application. Features: Search city, Display temperature, Display humidity, Display weather condition, Show weather icon. Use a free weather API. Generate HTML, CSS, JavaScript."""},
    {"name": "Beginner Test #6: Quiz App", "prompt": """Build a Quiz Application. Features: 5 multiple-choice questions, Next button, Score calculation, Result page, Restart quiz button. Use HTML, CSS, and JavaScript only."""},
    {"name": "Beginner Test #7: Personal Portfolio Website", "prompt": """Build a portfolio website. Sections: Home, About Me, Skills, Projects, Contact. Requirements: Responsive design, Smooth scrolling, Modern UI."""}
]

async def run_test(test):
    print(f"\n=============================================")
    print(f"Running: {test['name']}")
    print(f"=============================================")
    uri = "ws://localhost:8001/ws"
    try:
        async with websockets.connect(uri) as websocket:
            payload = {"type": "user_prompt", "prompt": test["prompt"]}
            await websocket.send(json.dumps(payload))
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                agent = data.get("agent", "system")
                status = data.get("status", "")
                message = data.get("data", {}).get("message", "")
                print(f"[{agent}] [{status}] {message}")
                
                if status == "error":
                    print(f"❌ TEST FAILED: {test['name']}")
                    return False
                if agent == "assembler" and status == "finished":
                    print(f"✅ TEST PASSED: {test['name']}")
                    return True
    except Exception as e:
        print(f"❌ ERROR connecting to websocket: {e}")
        return False

async def main():
    passed = 0
    failed = 0
    for test in TEST_CASES[:5]:
        success = await run_test(test)
        if success:
            passed += 1
        else:
            failed += 1
        
        print("Sleeping for 45 seconds to respect Gemini API rate limits...")
        await asyncio.sleep(45)
            
    print(f"\n=============================================")
    print(f"BATCH TEST SUMMARY: {passed} PASSED, {failed} FAILED")
    print(f"=============================================")

if __name__ == "__main__":
    asyncio.run(main())
