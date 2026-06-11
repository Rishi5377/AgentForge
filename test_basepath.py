import os
import subprocess
import time
import requests

def run_test():
    app_dir = "test-basepath-app"
    
    # Update next.config.mjs
    config_content = """
/** @type {import('next').NextConfig} */
const nextConfig = {
    basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
};
export default nextConfig;
"""
    with open(f"{app_dir}/next.config.mjs", "w") as f:
        f.write(config_content)
        
    print("Starting Next.js with NEXT_PUBLIC_BASE_PATH=/preview/test1234")
    
    env = os.environ.copy()
    env["NEXT_PUBLIC_BASE_PATH"] = "/preview/test1234"
    env["PORT"] = "3005"
    
    process = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=app_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(5) # wait for server to start
    
    try:
        # Test 1: Root without basepath
        try:
            r = requests.get("http://localhost:3005/")
            print(f"GET / -> {r.status_code}")
        except Exception as e:
            print(f"GET / -> ERROR {e}")
            
        # Test 2: Root with basepath
        try:
            r = requests.get("http://localhost:3005/preview/test1234")
            print(f"GET /preview/test1234 -> {r.status_code}")
        except Exception as e:
            print(f"GET /preview/test1234 -> ERROR {e}")
            
    finally:
        process.terminate()

if __name__ == "__main__":
    run_test()
