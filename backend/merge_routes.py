#!/usr/bin/env python3
import re
import shutil

# Backup
shutil.copy('main.py', 'main.py.backup')
print("✓ Backup created")

with open('main.py', 'r') as f:
    main_content = f.read()

with open('integrations_routes.py', 'r') as f:
    int_routes = f.read()

with open('admin_routes.py', 'r') as f:
    admin_routes = f.read()

# Find the last import statement in main.py
match = list(re.finditer(r'^from .* import .*$|^import .*$', main_content, re.MULTILINE))
if match:
    last_import_end = match[-1].end()
    insert_pos = main_content.find('\n', last_import_end) + 1
else:
    insert_pos = 0

# Extract imports we need to add
needed_imports = set()
for line in int_routes.split('\n'):
    if (line.startswith('from ') or line.startswith('import ')) and 'router' not in line and '__' not in line:
        needed_imports.add(line.strip())

for line in admin_routes.split('\n'):
    if (line.startswith('from ') or line.startswith('import ')) and 'router' not in line and '__' not in line:
        needed_imports.add(line.strip())

# Remove imports that are already in main.py
needed_imports = [i for i in needed_imports if i and i not in main_content]

print(f"✓ {len(needed_imports)} new imports to add")

# Extract route functions (everything after imports and before if __name__)
int_code_start = len([l for l in int_routes.split('\n') if l.startswith('from ') or l.startswith('import ')])
int_code = '\n'.join(int_routes.split('\n')[int_code_start:])

admin_code_start = len([l for l in admin_routes.split('\n') if l.startswith('from ') or l.startswith('import ')])
admin_code = '\n'.join(admin_routes.split('\n')[admin_code_start:])

# Clean up code (remove router definition lines)
int_code = '\n'.join([l for l in int_code.split('\n') if 'router' not in l.lower()])
admin_code = '\n'.join([l for l in admin_code.split('\n') if 'router' not in l.lower()])

# Find insertion point (before the first @app decorator in main.py)
route_match = re.search(r'^@app\..', main_content, re.MULTILINE)
if route_match:
    insert_pos = route_match.start()
else:
    # Insert before if __name__
    if_match = re.search(r'^if __name__', main_content, re.MULTILINE)
    if if_match:
        insert_pos = if_match.start()
    else:
        insert_pos = len(main_content)

# Build new imports section
imports_section = '\n'.join(needed_imports)
if imports_section:
    imports_section += '\n\n'

# Build new route section
routes_section = f'''\n# ========================\n# INTEGRATIONS & ADMIN ROUTES\n# ========================\n'''
routes_section += int_code + '\n\n' + admin_code

# Combine
new_main = main_content[:insert_pos] + imports_section + routes_section + main_content[insert_pos:]

# Write
with open('main.py', 'w') as f:
    f.write(new_main)

print("✓ main.py updated successfully")
print(f"✓ Integration code inserted at position {insert_pos}")
print(f"\nTotal new imports: {len(needed_imports)}")
print(f"Total lines added: ~{len(routes_section.split(chr(10)))}")

