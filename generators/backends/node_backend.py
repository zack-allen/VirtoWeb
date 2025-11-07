import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEMPLATE_DIR = os.path.join(ROOT, 'generators', 'templates', 'static')


class NodeBackend:
    """Scaffold a minimal Express app that serves static HTML files.

    This backend produces a small Node project with an `express` server that serves the
    generated `public/` folder. The generated project includes `package.json` and a tiny server.
    """

    def generate(self, ast, output_dir):
        out = os.path.abspath(output_dir)
        if os.path.exists(out):
            shutil.rmtree(out)
        os.makedirs(out, exist_ok=True)

        # Render static HTML into public/ using Jinja2 templates
        from .common import render_static_site
        public = os.path.join(out, 'public')
        render_static_site(ast, TEMPLATE_DIR, public)

        # package.json
        pkg = {
            'name': ast['project'].get('id', 'virtoweb-node-site'),
            'version': ast['project'].get('version', '0.0.1'),
            'main': 'server.js',
            'scripts': {'start': 'node server.js'},
            'dependencies': {'express': '^4.18.0'}
        }
        import json
        with open(os.path.join(out, 'package.json'), 'w', encoding='utf-8') as f:
            json.dump(pkg, f, indent=2)

        server_js = """
const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 3000;
app.use(express.static(path.join(__dirname, 'public')));
app.listen(port, () => console.log(`Server running on port ${port}`));
"""
        with open(os.path.join(out, 'server.js'), 'w', encoding='utf-8') as f:
            f.write(server_js)

        print('Node (Express) backend: generated project at', out)
