import os
import shutil
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEMPLATE_DIR = os.path.join(ROOT, 'generators', 'templates', 'static')


class StaticBackend:
    """Minimal static backend: writes HTML files and copies assets/CSS."""

    def generate(self, ast, output_dir):
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(['html', 'xml']))

        layouts = ast['layouts']
        components = ast['components']

        # clean
        out = os.path.abspath(output_dir)
        if os.path.exists(out):
            shutil.rmtree(out)
        os.makedirs(out, exist_ok=True)

        # copy assets included in templates/assets
        assets_src = os.path.join(TEMPLATE_DIR, 'assets')
        if os.path.exists(assets_src):
            shutil.copytree(assets_src, os.path.join(out, 'assets'))

        for p in ast['pages']:
            route = p.get('route', '/')
            if '{' in route and '}' in route:
                # param routes skipped in static backend
                continue
            if route == '/' or route == '':
                out_dir = out
            else:
                out_dir = os.path.join(out, route.lstrip('/'))
            os.makedirs(out_dir, exist_ok=True)
            layout_id = p.get('layout')
            layout = layouts.get(layout_id)
            layout_tmpl = layout.get('template') + '.html.j2'
            tmpl = env.get_template(layout_tmpl)

            rendered_regions = {}
            for region_name in layout.get('regions', []):
                parts = []
                for inst in (p.get('regions') or {}).get(region_name, []):
                    comp_id = inst.get('component')
                    comp = components.get(comp_id)
                    if not comp:
                        parts.append(f'<!-- Missing component {comp_id} -->')
                        continue
                    comp_tmpl = comp.get('template') + '.html.j2'
                    try:
                        comp_template = env.get_template(comp_tmpl)
                        props = dict(comp.get('props', {}))
                        props.update(inst.get('props') or {})
                        parts.append(comp_template.render(project=ast['project'], page=p, props=props, regions={}))
                    except Exception as e:
                        parts.append(f'<!-- component render error: {e} -->')
                rendered_regions[region_name] = '\n'.join(parts)

            html = tmpl.render(project=ast['project'], page=p, regions=rendered_regions)
            with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)

        print('Static backend: generated site at', out)
