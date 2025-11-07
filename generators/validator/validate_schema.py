"""
Simple schema validator + AST extractor for VirtoWeb schema v1.
Usage:
  python validate_schema.py path/to/site_schema.json

Outputs:
  - prints validation results
  - writes AST to generators/validator/ast.json
"""
import json
import os
import sys
from jsonschema import validate, ValidationError

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCHEMA_PATH = os.path.join(ROOT, 'generators', 'schema', 'v1', 'virtoweb.schema.json')
AST_OUT = os.path.join(os.path.dirname(__file__), 'ast.json')


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_schema(schema_def, instance):
    try:
        validate(instance=instance, schema=schema_def)
        return True, None
    except ValidationError as e:
        return False, e


def build_ast(instance):
    # Produce a minimal AST useful for backends: maps and lists keyed by id
    ast = {
        'project': instance.get('project', {}),
        'layouts': {l['id']: l for l in instance.get('layouts', [])},
        'components': {c['id']: c for c in instance.get('components', [])},
        'pages': instance.get('pages', []),
        'forms': {f['id']: f for f in instance.get('forms', [])},
        'assets': instance.get('assets', [])
    }
    # Simple cross-checks
    errors = []
    for p in ast['pages']:
        if p['layout'] not in ast['layouts']:
            errors.append(f"Page '{p.get('id')}' references unknown layout '{p.get('layout')}'")
        # validate components in regions
        for region, comps in (p.get('regions') or {}).items():
            for ci in comps:
                comp_id = ci.get('component')
                if comp_id not in ast['components']:
                    errors.append(f"Page '{p.get('id')}' region '{region}' references unknown component '{comp_id}'")
    return ast, errors


def main():
    if len(sys.argv) < 2:
        print('Usage: python validate_schema.py path/to/site_schema.json')
        sys.exit(2)

    site_path = sys.argv[1]
    if not os.path.isabs(site_path):
        site_path = os.path.abspath(site_path)

    if not os.path.exists(site_path):
        print('Schema file not found:', site_path)
        sys.exit(2)

    schema_def = load_json(SCHEMA_PATH)
    instance = load_json(site_path)

    ok, err = validate_schema(schema_def, instance)
    if not ok:
        print('Schema validation FAILED:')
        print(err)
        sys.exit(3)

    print('Schema validation: OK')

    ast, cross_errors = build_ast(instance)
    if cross_errors:
        print('Cross-check errors:')
        for e in cross_errors:
            print(' -', e)
    else:
        print('Cross-checks: OK')

    # Write AST
    with open(AST_OUT, 'w', encoding='utf-8') as f:
        json.dump(ast, f, indent=2)
    print('AST written to', AST_OUT)


if __name__ == '__main__':
    main()
