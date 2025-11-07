#!/usr/bin/env python3
"""
StudioOps Dashboard Bundler
============================

This script bundles the modular ES6 dashboard into a single HTML file
that works with the file:// protocol.

It combines:
- index.html structure
- css/styles.css (inlined)
- All js/*.js modules (inlined, with imports/exports removed)

Output: dashboard.html
"""

import re
import os

def read_file(filepath):
    """Read file content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return ""

def remove_imports_exports(js_content):
    """
    Remove ES6 import/export statements from JavaScript.
    Convert exports to global function declarations.
    """
    # Remove import statements
    js_content = re.sub(r'^import\s+.*?from\s+[\'"].*?[\'"];?\s*$', '', js_content, flags=re.MULTILINE)
    js_content = re.sub(r'^import\s+[\'"].*?[\'"];?\s*$', '', js_content, flags=re.MULTILINE)
    js_content = re.sub(r'^import\s*{[^}]*}\s*from\s*[\'"].*?[\'"];?\s*$', '', js_content, flags=re.MULTILINE)
    js_content = re.sub(r'^import\s+\*\s+as\s+\w+\s+from\s+[\'"].*?[\'"];?\s*$', '', js_content, flags=re.MULTILINE)

    # Convert "export function" to "function" (make global)
    js_content = re.sub(r'^export\s+function\s+', 'function ', js_content, flags=re.MULTILINE)

    # Convert "export const" to "const" or "let" to "var" for global scope
    js_content = re.sub(r'^export\s+(const|let)\s+', r'\1 ', js_content, flags=re.MULTILINE)

    # Remove standalone "export {" blocks
    js_content = re.sub(r'^export\s*{[^}]*};?\s*$', '', js_content, flags=re.MULTILINE)

    # Remove "export default"
    js_content = re.sub(r'^export\s+default\s+', '', js_content, flags=re.MULTILINE)

    # Remove comment-only lines that became empty
    lines = js_content.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Keep the line if it's not empty or if it's a comment
        if stripped or line.startswith('//') or line.startswith('/*') or line.startswith('*'):
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def bundle_dashboard():
    """Main bundling function."""
    print("=" * 70)
    print("  StudioOps Dashboard Bundler")
    print("=" * 70)
    print()

    # Read base HTML
    print("📄 Reading index.html...")
    html_content = read_file('index.html')
    if not html_content:
        print("❌ Error: Could not read index.html")
        return

    # Read CSS
    print("🎨 Reading css/styles.css...")
    css_content = read_file('css/styles.css')

    # Read JavaScript modules in dependency order
    js_modules = [
        'js/config.js',
        'js/data.js',
        'js/utils.js',
        'js/exports.js',
        'js/modals.js',
        'js/charts.js',
        'js/filters.js',
        'js/settings.js',
        'js/upload.js',
        'js/tabs.js',
        'js/main.js'
    ]

    print("📦 Reading and processing JavaScript modules...")
    js_combined = []

    for module_path in js_modules:
        if not os.path.exists(module_path):
            print(f"⚠️  Warning: {module_path} not found, skipping...")
            continue

        print(f"   ✓ Processing {module_path}")
        js_content = read_file(module_path)

        # Remove imports/exports
        js_content = remove_imports_exports(js_content)

        # Add module separator comment
        module_name = os.path.basename(module_path)
        separator = f"\n\n{'=' * 80}\n// {module_name.upper()}\n{'=' * 80}\n\n"
        js_combined.append(separator + js_content)

    combined_js = '\n'.join(js_combined)

    # Build the bundled HTML
    print("🔨 Building bundled HTML...")

    # Replace CSS link with inline CSS
    # Use a lambda to avoid issues with backslashes in CSS
    def css_replacer(match):
        return f'<style>\n{css_content}\n    </style>'

    html_content = re.sub(
        r'<link\s+rel="stylesheet"\s+href="css/styles\.css"\s*/?>',
        css_replacer,
        html_content
    )

    # Replace the script tag that loads main.js with all bundled JavaScript
    # Use a lambda to avoid issues with backslashes in JavaScript
    def js_replacer(match):
        return f'<script>\n{combined_js}\n    </script>'

    html_content = re.sub(
        r'<script\s+type="module"\s+src="js/main\.js"><\/script>',
        js_replacer,
        html_content
    )

    # Add a comment header
    header_comment = """<!--
╔══════════════════════════════════════════════════════════════════════════════╗
║                     STUDIOOPS DASHBOARD - BUNDLED VERSION                    ║
║                                                                              ║
║  This is a single-file bundled version of the StudioOps Dashboard.          ║
║  It works with the file:// protocol (no web server required).               ║
║                                                                              ║
║  For the modular ES6 version, use index.html with a web server.             ║
║                                                                              ║
║  Generated automatically by bundle.py                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
-->

"""

    # Insert header after DOCTYPE
    html_content = re.sub(
        r'(<!DOCTYPE html>)',
        r'\1\n' + header_comment,
        html_content,
        count=1
    )

    # Write the bundled file
    output_file = 'dashboard.html'
    print(f"💾 Writing {output_file}...")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Get file size
        file_size = os.path.getsize(output_file)
        file_size_kb = file_size / 1024
        file_size_mb = file_size_kb / 1024

        print()
        print("=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print(f"📦 Created: {output_file}")
        print(f"📏 Size: {file_size_kb:.1f} KB ({file_size_mb:.2f} MB)")
        print()
        print("🚀 You can now open dashboard.html directly in your browser!")
        print("   No web server required - works with file:// protocol")
        print("=" * 70)

    except Exception as e:
        print(f"❌ Error writing {output_file}: {e}")

if __name__ == '__main__':
    # Check if we're in the right directory
    if not os.path.exists('index.html'):
        print("❌ Error: index.html not found.")
        print("   Please run this script from the StudioOps directory.")
        exit(1)

    if not os.path.exists('js'):
        print("❌ Error: js/ directory not found.")
        print("   Please run this script from the StudioOps directory.")
        exit(1)

    if not os.path.exists('css'):
        print("❌ Error: css/ directory not found.")
        print("   Please run this script from the StudioOps directory.")
        exit(1)

    bundle_dashboard()
