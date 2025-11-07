"""
Core multi-language generator for VirtoWeb.

Responsibilities:
- load and validate schema against JSON Schema
- produce an intermediate AST
- dispatch to language-specific backend generators

This module is intentionally small and importable from CLI wrappers.
"""
import json
import os
from jsonschema import validate as js_validate, ValidationError

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCHEMA_PATH = os.path.join(ROOT, 'generators', 'schema', 'v1', 'virtoweb.schema.json')


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_schema(schema_def, instance):
    try:
        js_validate(instance=instance, schema=schema_def)
        return True, None
    except ValidationError as e:
        return False, e


def build_ast(instance):
    ast = {
        'project': instance.get('project', {}),
        'layouts': {l['id']: l for l in instance.get('layouts', [])},
        'components': {c['id']: c for c in instance.get('components', [])},
        'pages': instance.get('pages', []),
        'forms': {f['id']: f for f in instance.get('forms', [])},
        'assets': instance.get('assets', [])
    }
    errors = []
    for p in ast['pages']:
        if p['layout'] not in ast['layouts']:
            errors.append(f"Page '{p.get('id')}' references unknown layout '{p.get('layout')}'")
        for region, comps in (p.get('regions') or {}).items():
            for ci in comps:
                comp_id = ci.get('component')
                if comp_id not in ast['components']:
                    errors.append(f"Page '{p.get('id')}' region '{region}' references unknown component '{comp_id}'")
    return ast, errors


def get_backend(name):
    name = (name or '').lower()
    if name == 'static':
        from ..backends.static_backend import StaticBackend
        return StaticBackend()
    if name == 'python' or name == 'flask':
        from ..backends.python_backend import PythonBackend
        return PythonBackend()
    if name == 'node' or name == 'express':
        from ..backends.node_backend import NodeBackend
        return NodeBackend()
    if name == 'php':
        from ..backends.php_backend import PhpBackend
        return PhpBackend()
    raise ValueError(f'Unknown backend: {name}')


def generate(schema_path, backend_name=None, output_dir=None):
    schema_def = load_json(SCHEMA_PATH)
    instance = load_json(schema_path)

    ok, err = validate_schema(schema_def, instance)
    if not ok:
        raise RuntimeError(f'Schema validation failed: {err}')

    ast, cross_errors = build_ast(instance)
    if cross_errors:
        raise RuntimeError('Cross-check errors: ' + '; '.join(cross_errors))

    backend_name = backend_name or instance.get('generator', {}).get('language', 'static')
    output_dir = output_dir or instance.get('generator', {}).get('outputDir', 'dist/output')

    backend = get_backend(backend_name)
    backend.generate(ast, output_dir)
