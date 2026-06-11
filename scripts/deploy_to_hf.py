import os
import shutil
from huggingface_hub import HfApi

def get_hf_token():
    import subprocess
    try:
        result = subprocess.run(["git", "remote", "get-url", "huggingface"], capture_output=True, text=True, check=True)
        url = result.stdout.strip()
        if ":" in url and "@" in url:
            return url.split("://")[1].split("@")[0].split(":")[1]
    except Exception:
        pass
    return os.environ.get("HF_TOKEN", "")

def deploy():
    print("🚀 Preparing deployment to Hugging Face Spaces...")
    hf_token = get_hf_token()
    repo_id = "rishi-18/AgentForge"
    api = HfApi()

    print("📁 Copying necessary files to a temporary build folder...")
    if os.path.exists("hf_build"):
        shutil.rmtree("hf_build")
    os.makedirs("hf_build")
    
    # Copy backend folder
    shutil.copytree("backend", "hf_build/backend", ignore=shutil.ignore_patterns("workspace", "node_modules", ".next", "dist", "venv", "__pycache__"))
    
    # Copy Dockerfile
    shutil.copy("Dockerfile", "hf_build/Dockerfile")

    print(f"📦 Uploading backend files to {repo_id}...")
    
    try:
        api.upload_folder(
            folder_path="hf_build",
            repo_id=repo_id,
            repo_type="space",
            token=hf_token if hf_token else None,
            commit_message="Deploy Web Version Backend (Fast)",
            ignore_patterns=["*.pyc", "__pycache__/*", "*.png"]
        )
        print("✅ Deployment Successful!")
        print(f"🌍 Your backend is now live at: https://huggingface.co/spaces/{repo_id}")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")

if __name__ == "__main__":
    deploy()
