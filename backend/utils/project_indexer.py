import os

def generate_project_structure(workspace_dir: str) -> str:
    """
    Crawls the workspace and generates a markdown map of the codebase.
    Includes file paths and line counts, ignoring common build/dependency folders.
    """
    ignore_dirs = {'.git', 'node_modules', '.next', 'dist', 'build', '.gemini', 'scratch'}
    ignore_files = {'project_structure.md', 'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock'}
    
    structure_lines = ["# Project Structure Map\n"]
    structure_lines.append("This file serves as the structural index of the codebase for the Supervisor Agent.\n")
    
    for root, dirs, files in os.walk(workspace_dir):
        # Mutate dirs in-place to avoid traversing ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            if file in ignore_files or file.startswith('.'):
                continue
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, workspace_dir)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                structure_lines.append(f"- `{rel_path}` ({line_count} lines)")
            except Exception:
                # Skip binary files or unreadable files
                continue
                
    content = "\n".join(structure_lines)
    
    output_path = os.path.join(workspace_dir, "project_structure.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return content
