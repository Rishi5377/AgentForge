import glob
import re

for f in glob.glob('run_*_test.py') + glob.glob('run_expense_tracker.py'):
    with open(f, 'r') as file:
        content = file.read()
    
    # We messed up the previous injection, so let's clean it up
    content = re.sub(
        r'uri = f"ws://127\.0\.0\.1:\{os\.getenv\(\\\'PORT\\\', os\.getenv\(\\\'BACKEND_PORT\\\', 8001\)\)\}/ws"',
        r'port = os.getenv("PORT", os.getenv("BACKEND_PORT", 8001))\n    uri = f"ws://127.0.0.1:{port}/ws"',
        content
    )
    with open(f, 'w') as file:
        file.write(content)
    print(f"Fixed {f}")
