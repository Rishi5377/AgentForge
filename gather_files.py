import os

ignores = ['node_modules', 'venv', '.git', '__pycache__', '.next', 'dist', 'build', 'public', 'workspace']
valid_exts = ['.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.css', '.html']

out_path = 'scratch_codebase.txt'
with open(out_path, 'w', encoding='utf-8') as out:
    for root, dirs, files in os.walk('.'):
        if any(ig in root for ig in ignores):
            continue
        for f in files:
            if not any(f.endswith(ext) for ext in valid_exts):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                out.write(f'\n\n{"="*40}\nFILE: {path}\n{"="*40}\n')
                out.write(content)
            except Exception as e:
                out.write(f'\n\n[Error reading {path}: {e}]\n')
