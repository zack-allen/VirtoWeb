import os
import shutil
from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_static_site(ast, template_dir, out_public):
    """Render the site's pages using Jinja2 templates found in template_dir and write
    fully-rendered HTML files into out_public preserving route structure.

    Copies `assets/` from template_dir into out_public/assets.
    """
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape(['html', 'xml']))

    # prepare output
    out = os.path.abspath(out_public)
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)

    # copy template assets (styles etc.)
    assets_src = os.path.join(template_dir, 'assets')
    if os.path.exists(assets_src):
        shutil.copytree(assets_src, os.path.join(out, 'assets'))

    layouts = ast.get('layouts', {})
    components = ast.get('components', {})

    def render_component(inst, page):
        comp_id = inst.get('component')
        comp = components.get(comp_id)
        if not comp:
            return f'<!-- Missing component {comp_id} -->'
        tmpl_name = comp.get('template') + '.html.j2'
        try:
            tmpl = env.get_template(tmpl_name)
        except Exception as e:
            return f'<!-- Component template load error {tmpl_name}: {e} -->'
        props = dict(comp.get('props', {}))
        props.update(inst.get('props') or {})
        return tmpl.render(project=ast.get('project', {}), page=page, props=props, regions={})

    for p in ast.get('pages', []):
        route = p.get('route', '/')
        if '{' in route and '}' in route:
            # skip parameterized routes for now
            continue
        if route == '/' or route == '':
            out_dir = out
        else:
            out_dir = os.path.join(out, route.lstrip('/'))
        os.makedirs(out_dir, exist_ok=True)

        layout_id = p.get('layout')
        layout = layouts.get(layout_id)
        if not layout:
            # write a basic page
            with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(f"<h1>Missing layout {layout_id}</h1>")
            continue

        layout_tmpl = layout.get('template') + '.html.j2'
        try:
            layout_template = env.get_template(layout_tmpl)
        except Exception as e:
            with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(f"<!-- Layout template load error {layout_tmpl}: {e} -->")
            continue

        rendered_regions = {}
        for region_name in layout.get('regions', []):
            parts = []
            for inst in (p.get('regions') or {}).get(region_name, []):
                parts.append(render_component(inst, p))
            rendered_regions[region_name] = '\n'.join(parts)

        html = layout_template.render(project=ast.get('project', {}), page=p, regions=rendered_regions)
        with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
