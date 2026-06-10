import os
import subprocess

ws = 'c:/Users/lenovo/Downloads/AgentForge/backend/workspace'
app_dirs = [os.path.join(ws, d) for d in os.listdir(ws) if d.startswith('app_') and os.path.isdir(os.path.join(ws, d))]

for app in app_dirs[:5]: # just sample 5
    print(f"\n{'='*50}\nTesting {os.path.basename(app)}\n{'='*50}")
    pkg = os.path.join(app, "package.json")
    if not os.path.exists(pkg):
        print("No package.json found")
        continue
        
    print("Running tsc --noEmit...")
    res = subprocess.run(["npx.cmd" if os.name == "nt" else "npx", "tsc", "--noEmit"], cwd=app, capture_output=True, text=True)
    if res.returncode != 0:
        print("TSC Error:")
        print(res.stdout + res.stderr)
        continue
        
    print("Running npm run build...")
    res = subprocess.run(["npm.cmd" if os.name == "nt" else "npm", "run", "build"], cwd=app, capture_output=True, text=True)
    if res.returncode != 0:
        print("Build Error:")
        print(res.stdout + res.stderr)
        continue
        
    print("Build successful.")
