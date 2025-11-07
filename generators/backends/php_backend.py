import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEMPLATE_DIR = os.path.join(ROOT, 'generators', 'templates', 'static')


class PhpBackend:
    """Scaffold a minimal PHP project that serves generated templates.

    The PHP backend will copy static templates into a public folder and add a simple index.php
    that uses PHP's include to render static HTML fragments.
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

        index_php = """
<?php
// Minimal router that serves files from public/ and falls back to index.html
$uri = urldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$path = __DIR__ . '/public' . $uri;
if ($uri === '/' || $uri === '') {
    $path = __DIR__ . '/public/index.html';
} elseif (is_dir($path)) {
    $path = rtrim($path, '/') . '/index.html';
}
if (file_exists($path)) {
    header('Content-Type: text/html; charset=utf-8');
    echo file_get_contents($path);
    exit;
}
http_response_code(404);
echo 'Not found';
?>
"""
        with open(os.path.join(out, 'index.php'), 'w', encoding='utf-8') as f:
            f.write(index_php)

        print('PHP backend: generated project at', out)
