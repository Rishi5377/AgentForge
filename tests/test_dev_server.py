import os
import subprocess
import time

ws = 'c:/Users/lenovo/Downloads/AgentForge/backend/workspace/app_07f69d75-c342-4c02-8ec8-d4f335376839'
print(f"Testing dev server in {ws}")

process = subprocess.Popen(["npm.cmd" if os.name == "nt" else "npm", "run", "dev", "--", "--port", "50212"], cwd=ws, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

start = time.time()
lines = []
while time.time() - start < 10:
    # Read non-blocking if possible, or just wait 5 secs and terminate
    pass

process.terminate()
try:
    stdout, stderr = process.communicate(timeout=5)
    print("STDOUT:")
    print(stdout)
    print("STDERR:")
    print(stderr)
except Exception as e:
    print("Error getting output:", e)
