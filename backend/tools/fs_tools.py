import os
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

def _get_workspace(config: RunnableConfig) -> str:
    workspace_dir = config.get("configurable", {}).get("workspace_dir")
    if not workspace_dir:
        raise ValueError("workspace_dir not provided in RunnableConfig.")
    return workspace_dir

def _resolve_path(workspace_dir: str, filepath: str) -> str:
    """Safely resolve the file path within the workspace."""
    # Prevent path traversal
    full_path = os.path.abspath(os.path.join(workspace_dir, filepath))
    if not full_path.startswith(os.path.abspath(workspace_dir)):
        raise PermissionError(f"Access denied: {filepath} is outside the workspace.")
    return full_path

@tool
def read_file(filepath: str, config: RunnableConfig) -> str:
    """Read the contents of a specific file in the workspace.
    
    Args:
        filepath: The relative path to the file (e.g., 'src/App.jsx').
    """
    try:
        workspace = _get_workspace(config)
        full_path = _resolve_path(workspace, filepath)
        
        if not os.path.exists(full_path):
            return f"Error: File not found at {filepath}"
        
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def write_file(filepath: str, content: str, config: RunnableConfig) -> str:
    """Write or overwrite a file in the workspace.
    
    Args:
        filepath: The relative path to the file (e.g., 'src/App.jsx').
        content: The full content to write to the file.
    """
    try:
        workspace = _get_workspace(config)
        full_path = _resolve_path(workspace, filepath)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def list_dir(directory: str, config: RunnableConfig) -> str:
    """List the files and folders in a specific directory within the workspace.
    
    Args:
        directory: The relative path to the directory. Use '.' for the root of the workspace.
    """
    try:
        workspace = _get_workspace(config)
        full_path = _resolve_path(workspace, directory)
        
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return f"Error: Directory not found at {directory}"
        
        items = os.listdir(full_path)
        # Exclude hidden and massive folders
        items = [i for i in items if not i.startswith(".") and i != "node_modules"]
        return "Directory contents:\n" + "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

TOOLS = [read_file, write_file, list_dir]
