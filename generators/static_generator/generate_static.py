"""
Minimal static site generator for VirtoWeb example schemas.
- Validates schema using the project JSON Schema
- Renders pages using Jinja2 templates found under generators/templates/static

Usage:
  python generate_static.py path/to/site_schema.json

Limitations:
- Only supports static, non-parameterized routes (no {slug} expansion)
- Assumes templates follow the naming convention: <template>.html.j2
"""
import json
import os
import sys
import shutil
from jsonschema import validate, ValidationError
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCHEMA_PATH = os.path.join(ROOT, 'generators', 'schema', 'v1', 'virtoweb.schema.json')
TEMPLATE_DIR = os.path.join(ROOT, 'generators', 'templates', 'static')


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_schema(schema_def, instance):
    try:
        validate(instance=instance, schema=schema_def)
        return True, None
    except ValidationError as e:
        return False, e


def template_name_to_file(tname):
    # convert 'layouts/main' -> 'layouts/main.html.j2'
    return tname + '.html.j2'


def render_component(env, components_map, instance):
    comp_id = instance.get('component')
    comp_def = components_map.get(comp_id)
    if not comp_def:
        return f"<!-- Missing component: {comp_id} -->"
    tmpl_name = template_name_to_file(comp_def.get('template'))
    try:
        tmpl = env.get_template(tmpl_name)
    except Exception as e:
        return f"<!-- Template load error for {tmpl_name}: {e} -->"
    # merge props
    props = dict(comp_def.get('props', {}))
    props.update(instance.get('props') or {})
    ctx = {'project': project, 'props': props, 'page': page}
    return tmpl.render(**ctx)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python generate_static.py path/to/site_schema.json')
        sys.exit(2)

    site_path = sys.argv[1]
    if not os.path.isabs(site_path):
        site_path = os.path.abspath(site_path)

    schema_def = load_json(SCHEMA_PATH)
    instance = load_json(site_path)

    ok, err = validate_schema(schema_def, instance)
    if not ok:
        print('Schema validation FAILED:')
        print(err)
        sys.exit(3)

    project = instance.get('project', {})
    generator_opts = instance.get('generator', {})
    output_dir = os.path.abspath(generator_opts.get('outputDir', 'dist/static-output'))

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )

    layouts = {l['id']: l for l in instance.get('layouts', [])}
    components_map = {c['id']: c for c in instance.get('components', [])}

    # Clean output dir
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Copy any assets
    for asset in instance.get('assets', []):
        src = os.path.join(ROOT, asset['src']) if not os.path.isabs(asset['src']) else asset['src']
        dest_path = os.path.join(output_dir, asset['dest'])
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        try:
            shutil.copy2(src, dest_path)
            print(f'Copied asset {src} -> {dest_path}')
        except Exception as e:
            print(f'Warning: failed to copy asset {src}: {e}')

    # Render pages
    for p in instance.get('pages', []):
        page = p
        route = p.get('route', '/')
        if '{' in route and '}' in route:
            print(f"Skipping parameterized route {route} (not supported by minimal static generator)")
            continue
        # output path
        if route == '/' or route == '':
            out_dir = output_dir
        else:
            out_dir = os.path.join(output_dir, route.lstrip('/'))
        os.makedirs(out_dir, exist_ok=True)
        layout_id = p.get('layout')
        layout = layouts.get(layout_id)
        if not layout:
            print(f"Skipping page {p.get('id')}: unknown layout {layout_id}")
            continue
        layout_tmpl = template_name_to_file(layout.get('template'))
        try:
            tmpl = env.get_template(layout_tmpl)
        except Exception as e:
            print(f"Error loading layout template {layout_tmpl} for page {p.get('id')}: {e}")
            continue
        # render regions
        rendered_regions = {}
        for region_name in layout.get('regions', []):
            rendered_parts = []
            for inst in (p.get('regions') or {}).get(region_name, []):
                rendered_parts.append(render_component(env, components_map, inst))
            rendered_regions[region_name] = '\n'.join(rendered_parts)
        ctx = {
            'project': project,
            'page': p,
            'regions': rendered_regions
        }
        out_html = tmpl.render(**ctx)
        out_file = os.path.join(out_dir, 'index.html')
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(out_html)
        print('Wrote', out_file)

    print('Static generation complete. Output dir:', output_dir)
