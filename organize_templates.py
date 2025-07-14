import os
import shutil
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
templates_dir = BASE_DIR / 'templates'
static_dir = BASE_DIR / 'static'

# Create user and dealer directories if they don't exist
for role in ['user', 'dealer']:
    (templates_dir / role).mkdir(exist_ok=True)
    (static_dir / 'js' / role).mkdir(parents=True, exist_ok=True)
    (static_dir / 'styles' / role).mkdir(parents=True, exist_ok=True)

# Files to copy (relative to templates/)
template_files = [
    'cart.html',
    'company_selection.html',
    'product_selection.html',
    'quotation.html',
    'profile/profile.html',
    'products/blankets/blankets.html',
    'products/chemicals/mpack.html',
    'components/company_info.html'
]

# Copy template files to user and dealer directories
for file_path in template_files:
    src = templates_dir / file_path
    if src.exists():
        for role in ['user', 'dealer']:
            dst = templates_dir / role / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"Copied {src} to {dst}")

# JavaScript files to copy (relative to static/js/)
js_files = [
    'blankets.js',
    'cart.js',
    'company_info.js',
    'company_selection.js',
    'mpack.js',
    'product_selection.js',
    'quotation.js',
    'selection.js',
    'dashboard.js'
]

# Copy JavaScript files to user and dealer directories
for js_file in js_files:
    src = static_dir / 'js' / js_file
    if src.exists():
        for role in ['user', 'dealer']:
            dst = static_dir / 'js' / role / js_file
            shutil.copy2(src, dst)
            print(f"Copied {src} to {dst}")

# Update template references in HTML files
def update_template_references():
    for role in ['user', 'dealer']:
        for root, _, files in os.walk(templates_dir / role):
            for file in files:
                if file.endswith('.html'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Update static file references
                        content = content.replace('href="/static/styles/', f'href="/static/styles/{role}/')
                        content = content.replace('src="/static/js/', f'src="/static/js/{role}/')
                        
                        # Update template extends and includes
                        if role == 'dealer':
                            content = content.replace('{% extends "', '{% extends "dealer/')
                            content = content.replace('{% include "', '{% include "dealer/')
                        else:
                            content = content.replace('{% extends "', '{% extends "user/')
                            content = content.replace('{% include "', '{% include "user/')
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Updated references in {file_path}")
                    except Exception as e:
                        print(f"Error updating {file_path}: {e}")

print("\nUpdating template references...")
update_template_references()
print("\nTemplate organization complete!")
