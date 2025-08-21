import os
import sys
import io

def list_structure(startpath='.', ignore_dirs=None, depth=10):
    ignore_dirs = set(ignore_dirs or ["__pycache__", ".git", "env", "venv", "migrations"])
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        level = root.replace(startpath, '').count(os.sep)
        if level >= depth:
            continue
        indent = '│   ' * level + '├── '
        print(f"{indent}{os.path.basename(root)}/")

        subindent = '│   ' * (level + 1) + '├── '
        for f in files:
            if f.endswith(('.pyc', '.db')):
                continue
            print(f"{subindent}{f}")

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    list_structure(startpath='.')
