import ast
import os
import sys

stdlib = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()

project_dirs = ['reader', 'config']
imports = set()

for d in project_dirs:
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    try:
                        tree = ast.parse(file.read(), filename=path)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for n in node.names:
                                    imports.add(n.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom):
                                if node.module and node.level == 0:
                                    imports.add(node.module.split('.')[0])
                    except Exception as e:
                        pass

external_imports = imports - stdlib - {'reader', 'config'}
print("External imports found:", external_imports)
