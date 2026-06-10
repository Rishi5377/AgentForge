import glob
import re

for f in glob.glob('run_*_test.py') + glob.glob('run_expense_tracker.py'):
    with open(f, 'r') as file:
        content = file.read()
    
    if 'ws://localhost:' in content:
        if 'import os' not in content:
            content = 'import os\n' + content
        content = re.sub(
            r'"ws://localhost:\d+/ws"',
            r'f"ws://127.0.0.1:{os.getenv(\'PORT\', os.getenv(\'BACKEND_PORT\', 8001))}/ws"',
            content
        )
        with open(f, 'w') as file:
            file.write(content)
        print(f"Fixed {f}")
