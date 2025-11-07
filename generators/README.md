# VirtoWeb Generators (minimal)

This folder contains minimal helper scripts and templates to validate a VirtoWeb schema and produce a basic static HTML output.

Quick start (Windows PowerShell):

1. Create a virtual environment and activate it

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install requirements

```powershell
pip install -r generators/static_generator/requirements.txt
```

3. Validate the example schema

```powershell
python generators/validator/validate_schema.py examples/example_layout_site.json
```

4. Generate a static site

```powershell
python generators/static_generator/generate_static.py examples/example_layout_site.json
```

Output will be written to the `outputDir` configured in the schema (e.g. `dist/static-example`).

4. Generate a static site (or other language projects)

Using the minimal single-backend script:

```powershell
# generate according to the 'generator.language' field in the schema (static, python, node, php)
python -c "from generators.core.generator import generate; generate('examples/example_layout_site.json')"
```

Or explicitly choose a backend and output directory:

```powershell
python -c "from generators.core.generator import generate; generate('examples/example_layout_site.json', backend_name='python', output_dir='dist/example-flask')"
```

Output will be written to the `outputDir` configured in the schema (e.g. `dist/static-example`) or the explicit path you pass.

Notes:
- This is a minimal reference implementation meant for developer iteration. It intentionally keeps behavior simple and explicit.
- The static generator does not expand parameterized routes (e.g., `/posts/{slug}`) and does not implement server-side form handling. Use it as a starting point for full backends.
