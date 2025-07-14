import os
import shutil
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
templates_dir = BASE_DIR / 'templates'
static_dir = BASE_DIR / 'static'

# Files to move to user and dealer directories
user_files = [
    'cart.html',
    'company_selection.html',
    'product_selection.html',
    'quotation.html',
    'profile/profile.html',
    'products/blankets/blankets.html',
    'products/chemicals/mpack.html',
    'components/company_info.html'
]

# Create necessary directories
def create_directories():
    # Create user and dealer directories
    for role in ['user', 'dealer']:
        (templates_dir / role / 'products/blankets').mkdir(parents=True, exist_ok=True)
        (templates_dir / role / 'products/chemicals').mkdir(parents=True, exist_ok=True)
        (templates_dir / role / 'components').mkdir(parents=True, exist_ok=True)
        (templates_dir / role / 'profile').mkdir(parents=True, exist_ok=True)
        
        # Create static directories
        (static_dir / 'js' / role).mkdir(parents=True, exist_ok=True)
        (static_dir / 'styles' / role).mkdir(parents=True, exist_ok=True)

def move_template_files():
    for role in ['user', 'dealer']:
        for file_path in user_files:
            src = templates_dir / file_path
            if src.exists():
                dst = templates_dir / role / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print(f"Copied {src} to {dst}")

def move_static_files():
    # Move JS files
    js_files = [
        'blankets.js',
        'cart.js',
        'company_info.js',
        'company_selection.js',
        'mpack.js',
        'product_selection.js',
        'quotation.js',
        'selection.js'
    ]
    
    for role in ['user', 'dealer']:
        for js_file in js_files:
            src = static_dir / 'js' / js_file
            if src.exists():
                dst = static_dir / 'js' / role / js_file
                shutil.copy2(src, dst)
                print(f"Copied {src} to {dst}")
    
    # Move CSS files
    css_files = ['login.css', 'signup.css', 'forgot-password.css', 'styles.css']
    for role in ['user', 'dealer']:
        for css_file in css_files:
            src = static_dir / 'styles' / css_file
            if src.exists():
                dst = static_dir / 'styles' / role / css_file
                shutil.copy2(src, dst)
                print(f"Copied {src} to {dst}")

def update_template_references():
    # Update template references in user and dealer directories
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

def main():
    print("Creating directories...")
    create_directories()
    
    print("\nCopying template files...")
    move_template_files()
    
    print("\nCopying static files...")
    move_static_files()
    
    print("\nUpdating template references...")
    update_template_references()
    
    print("\nFile organization complete!")

if __name__ == "__main__":
    main()
