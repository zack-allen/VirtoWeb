import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEMPLATE_DIR = os.path.join(ROOT, 'generators', 'templates', 'static')


class PythonBackend:
    """Generate a minimal Flask app from the AST.

    Output structure:
      <out>/
        app.py
        requirements.txt
        templates/...
        static/...
"""

    def generate(self, ast, output_dir):
        out = os.path.abspath(output_dir)
        if os.path.exists(out):
            shutil.rmtree(out)
        os.makedirs(out, exist_ok=True)

        # Render a fully static public/ folder (pre-render Jinja templates to HTML)
        from .common import render_static_site

        public_dir = os.path.join(out, 'public')
        render_static_site(ast, TEMPLATE_DIR, public_dir)

        # write a minimal Flask app that serves the generated public/ folder
        app_py = """
from flask import Flask, send_from_directory
import os
app = Flask(__name__, static_folder='public', static_url_path='')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    # send static files from public/
    full = os.path.join(app.static_folder, path)
    if os.path.isdir(full):
        return send_from_directory(app.static_folder, os.path.join(path, 'index.html'))
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
"""

        with open(os.path.join(out, 'app.py'), 'w', encoding='utf-8') as f:
            f.write(app_py)

        # requirements
        with open(os.path.join(out, 'requirements.txt'), 'w', encoding='utf-8') as f:
            f.write('Flask\n')

        print('Python (Flask) backend: generated project at', out)
