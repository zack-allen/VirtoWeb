# VirtoWeb — Local code-generator for multi-language websites

VirtoWeb is an open-source, developer-first local website generator that converts a single unified JSON project schema into complete, self-hostable source-code projects across multiple backend languages (PHP, Node.js, Python/Flask, and static HTML/CSS/JS).

This repository contains:

- generators/: core schema, multi-backend generators, templates and example schemas
- builders/: a prototype cross-platform desktop builder (PyQt6) for visually composing sites and exporting schema JSON
- examples/: sample VirtoWeb project schemas
- docs/: human-readable schema docs and reference material

The goal: let designers and developers declare a site as JSON (pages, routes, components, layouts, forms, assets) and produce runnable projects in different languages with consistent folder structures and templates.

Why VirtoWeb?
- Single source of truth: author your site once in JSON and generate language-specific projects.
- Minimal dependencies in generated projects.
- Cross-language parity: same pages/layouts/components across outputs.
- Local-first: the generator runs locally; no hosting required.

Quick start (developer machine)

Requirements: Python 3.10+ (3.14 supported), Git, and optional packaging tools (PyInstaller, npm) for packaging or running generated Node projects.

1. Clone the repo

```powershell
git clone https://github.com/zack-allen/VirtoWeb.git
cd VirtoWeb
```

2. Create and activate a Python virtual environment

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

3. Install generator dependencies (jsonschema + Jinja2)

```powershell
pip install -r .\generators\static_generator\requirements.txt
```

4. Validate the example schema

```powershell
python .\generators\validator\validate_schema.py .\examples\example_layout_site.json
```

5. Generate a site (default backend declared in schema: `static`)

```powershell
python -c "from generators.core.generator import generate; generate('examples/example_layout_site.json')"
```

6. Generate a specific backend (python, node, php, static)

```powershell
# Flask (Python)
python -c "from generators.core.generator import generate; generate('examples/example_layout_site.json', backend_name='python', output_dir='dist/example-flask')"

# Node (Express)
python -c "from generators.core.generator import generate; generate('examples/example_layout_site.json', backend_name='node', output_dir='dist/example-node')"

# PHP
python -c "from generators.core.generator import generate; generate('examples/example_layout_site.json', backend_name='php', output_dir='dist/example-php')"
```

Running generated projects

- Static: open `dist/.../index.html` or use a static server.
- Flask:

```powershell
cd dist/example-flask
python app.py
# open http://127.0.0.1:5000/
```

- Node (Express):

```powershell
cd dist/example-node
npm install
npm start
# open http://localhost:3000/
```

- PHP (built-in server):

```powershell
cd dist/example-php
php -S localhost:8080
# open http://localhost:8080/
```

Repository layout (high level)

- generators/
  - schema/v1/virtoweb.schema.json — machine-readable JSON Schema (draft-07)
  - validator/ — schema validator + small AST extractor
  - core/generator.py — core entrypoint that validates and dispatches to backends
  - backends/ — language-specific generator backends (static, python, node, php)
  - templates/ — language-appropriate template files (Jinja2 used as primary templating source)
- builders/desktop_builder/ — PyQt6-based desktop prototype (drag/drop components, pages, export schema)
- examples/ — sample schemas demonstrating layouts, components, and forms
- docs/ — human-readable schema docs and guidance

Schema & templates

VirtoWeb is driven by a single JSON schema (see `generators/schema/v1/virtoweb.schema.json`). The schema describes:
- project metadata
- assets to include or copy
- layouts (template names + regions)
- components (template references + default props)
- pages (route, layout, and region content)
- forms (definitions that backends can implement securely)

Backends consume an intermediate AST produced by the core generator and produce language-specific output. Templates living under `generators/templates/static/` act as canonical Jinja2 templates which are pre-rendered into static HTML for runtimes that don't support Jinja (Node/PHP). The static backend and shared renderer ensure parity across generated sites.

Desktop builder

The `builders/desktop_builder` directory contains a PyQt6 prototype that lets you visually build pages and export a valid VirtoWeb JSON schema. It is a prototype intended for local development and to seed a future web-based builder.

Packaging the builder

Use PyInstaller to produce native executables for Windows/macOS/Linux. Packaging and distribution specifics depend on your target platform; test generated artifacts on clean hosts.

Contribution guide

We welcome contributions. Please follow these steps:

1. Fork the repository and create a feature branch.
2. Run and add tests where appropriate (we'll add a tests/ folder soon).
3. Open a PR with a clear description and link to any relevant issues.

Coding conventions

- Keep generated projects free of heavy runtime frameworks unless requested.
- Prefer clear, readable template output and predictable folder layout.

Roadmap (short term)

- Build a `virtoweb` CLI (init, validate, build, serve)
- Add unit tests & CI (GitHub Actions)
- Make builder multi-region and add live-preview (embedding the generator)
- Expand sample schema gallery (blog, ecommerce landing, docs site)

Security notes

- Generated projects should not auto-deploy or transmit secrets.
- Form handlers in generated backends include basic CSRF defaults where applicable, but you must review and harden these endpoints before production use.

License

This project is open-source and provided under the MIT License. See `LICENSE` for details (add a license file to the repo if not present).

Contact

If you have questions, file an issue or reach me via the repository contact details.

Acknowledgements

This project is an independent open-source effort to make multi-language code generation practical for local development.
