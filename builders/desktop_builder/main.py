"""
VirtoWeb Desktop Builder (prototype)

Features:
- Palette of components (load from an existing VirtoWeb schema)
- Pages list (create/select pages)
- Drag components from palette into the page canvas
- Select a placed component and edit its props (JSON)
- Export the resulting project schema as JSON compatible with VirtoWeb

This prototype uses PyQt6 (Qt6). To run:
  pip install -r requirements.txt
  python main.py

Packaging: use PyInstaller to create executables for each platform.
"""
import json
import os
import sys
from functools import partial

from PyQt6.QtWidgets import (
    QApplication, QWidget, QListWidget, QListWidgetItem, QPushButton,
    QHBoxLayout, QVBoxLayout, QFileDialog, QLabel, QTextEdit, QInputDialog,
    QMessageBox, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag


class DraggableListWidget(QListWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return
        data = QMimeData()
        role = int(Qt.ItemDataRole.UserRole)
        payload = json.dumps({'component': item.data(role)})
        data.setData('application/x-virtoweb-component', payload.encode('utf-8'))
        drag = QDrag(self)
        drag.setMimeData(data)
        # exec without explicit action for broader compatibility
        drag.exec()


class CanvasListWidget(QListWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-virtoweb-component'):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat('application/x-virtoweb-component'):
            payload = event.mimeData().data('application/x-virtoweb-component')
            try:
                obj = json.loads(bytes(payload).decode('utf-8'))
            except Exception:
                return
            comp_id = obj.get('component')
            item = QListWidgetItem(f"{comp_id}")
            # store instance data (component id + props)
            role = int(Qt.ItemDataRole.UserRole)
            item.setData(role, {'component': comp_id, 'props': {}})
            self.addItem(item)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class BuilderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('VirtoWeb Desktop Builder (prototype)')
        self.resize(1000, 600)

        # state
        self.schema = None
        self.components = {}  # id -> def
        self.pages = {}  # page_id -> list of component instances
        self.current_page = None

        # UI
        palette = QVBoxLayout()
        palette.addWidget(QLabel('Components'))
        self.comp_list = DraggableListWidget()
        palette.addWidget(self.comp_list)
        btn_load = QPushButton('Load schema...')
        btn_load.clicked.connect(self.load_schema)
        palette.addWidget(btn_load)

        middle = QVBoxLayout()
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel('Pages'))
        self.page_combo = QComboBox()
        self.page_combo.currentTextChanged.connect(self.on_page_selected)
        hdr.addWidget(self.page_combo)
        btn_new_page = QPushButton('New Page')
        btn_new_page.clicked.connect(self.new_page)
        hdr.addWidget(btn_new_page)
        middle.addLayout(hdr)

        self.canvas = CanvasListWidget()
        self.canvas.itemClicked.connect(self.on_canvas_item_selected)
        middle.addWidget(QLabel('Canvas (drop components here)'))
        middle.addWidget(self.canvas)

        right = QVBoxLayout()
        right.addWidget(QLabel('Component props (JSON)'))
        self.props_editor = QTextEdit()
        right.addWidget(self.props_editor)
        btn_apply = QPushButton('Apply props to selected')
        btn_apply.clicked.connect(self.apply_props)
        right.addWidget(btn_apply)

        btn_export = QPushButton('Export schema JSON')
        btn_export.clicked.connect(self.export_schema)
        right.addWidget(btn_export)

        btn_save = QPushButton('Save project file')
        btn_save.clicked.connect(self.save_project_file)
        right.addWidget(btn_save)

        layout = QHBoxLayout(self)
        L = QWidget(); L.setLayout(palette)
        M = QWidget(); M.setLayout(middle)
        R = QWidget(); R.setLayout(right)
        layout.addWidget(L, 1)
        layout.addWidget(M, 2)
        layout.addWidget(R, 1)

        # load default components
        self.load_default_components()

    def load_default_components(self):
        # Use the example schema bundled earlier if available
        default = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'example_layout_site.json'))
        if os.path.exists(default):
            self.load_schema_from_path(default)
        else:
            # fallback hardcoded
            comps = [
                {'id': 'nav', 'template': 'components/nav', 'props': {'links': []}},
                {'id': 'hero', 'template': 'components/hero', 'props': {'headline': 'Welcome'}},
                {'id': 'content', 'template': 'components/content', 'props': {'html': '<p>Content</p>'}},
            ]
            self.set_components(comps)

    def load_schema(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open VirtoWeb schema', os.getcwd(), 'JSON Files (*.json)')
        if not path:
            return
        self.load_schema_from_path(path)

    def load_schema_from_path(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load schema: {e}')
            return
        self.schema = data
        comps = data.get('components', [])
        self.set_components(comps)
        # create pages if present
        self.pages = {}
        for p in data.get('pages', []):
            pid = p.get('id')
            # convert regions into single 'main' list for the builder
            regions = p.get('regions', {})
            main_list = regions.get('main', [])
            instances = [{'component': ci.get('component'), 'props': ci.get('props', {})} for ci in main_list]
            self.pages[pid] = instances
        self.refresh_pages_ui()

    def set_components(self, comps):
        self.components = {c['id']: c for c in comps}
        self.comp_list.clear()
        for cid, cdef in self.components.items():
            item = QListWidgetItem(cid)
            role = int(Qt.ItemDataRole.UserRole)
            item.setData(role, cid)
            self.comp_list.addItem(item)

    def refresh_pages_ui(self):
        self.page_combo.clear()
        for pid in self.pages.keys():
            self.page_combo.addItem(pid)
        if self.page_combo.count() == 0:
            self.new_page()

    def new_page(self):
        name, ok = QInputDialog.getText(self, 'New Page', 'Enter page id (e.g. home):')
        if not ok or not name:
            return
        if name in self.pages:
            QMessageBox.warning(self, 'Exists', 'Page id already exists')
            return
        self.pages[name] = []
        self.page_combo.addItem(name)
        self.page_combo.setCurrentText(name)

    def on_page_selected(self, text):
        self.current_page = text
        self.load_canvas_for_page(text)

    def load_canvas_for_page(self, page_id):
        self.canvas.clear()
        if not page_id:
            return
        for inst in self.pages.get(page_id, []):
            item = QListWidgetItem(inst.get('component'))
            role = int(Qt.ItemDataRole.UserRole)
            item.setData(role, inst)
            self.canvas.addItem(item)

    def on_canvas_item_selected(self, item):
        role = int(Qt.ItemDataRole.UserRole)
        inst = item.data(role)
        self.props_editor.setPlainText(json.dumps(inst.get('props', {}), indent=2))

    def apply_props(self):
        item = self.canvas.currentItem()
        if not item:
            return
        txt = self.props_editor.toPlainText()
        try:
            obj = json.loads(txt) if txt.strip() else {}
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Invalid JSON: {e}')
            return
        role = int(Qt.ItemDataRole.UserRole)
        inst = item.data(role)
        inst['props'] = obj
        item.setData(role, inst)

    def export_schema(self):
        # Build a minimal schema containing project, layouts, components, pages
        project = {'id': 'builder-output', 'title': 'Builder Output', 'version': '1.0.0'}
        layouts = [
            {'id': 'main', 'template': 'layouts/main', 'regions': ['head', 'header', 'main', 'footer'], 'default': True}
        ]
        components = list(self.components.values())
        pages = []
        for pid, instances in self.pages.items():
            regions = {'main': [{'component': i['component'], 'props': i.get('props', {})} for i in instances]}
            pages.append({'id': pid, 'route': '/' + ('' if pid == 'home' else pid), 'title': pid.title(), 'layout': 'main', 'regions': regions})

        out = {'project': project, 'layouts': layouts, 'components': components, 'pages': pages}
        path, _ = QFileDialog.getSaveFileName(self, 'Export schema JSON', os.getcwd(), 'JSON Files (*.json)')
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(out, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to write file: {e}')
            return
        QMessageBox.information(self, 'Exported', f'Wrote schema to {path}')

    def save_project_file(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save project (.vwb.json)', os.getcwd(), 'JSON Files (*.json)')
        if not path:
            return
        # Save internal project (includes placed components)
        data = {'components': list(self.components.values()), 'pages': []}
        for pid, instances in self.pages.items():
            data['pages'].append({'id': pid, 'regions': {'main': instances}})
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save project: {e}')
            return
        QMessageBox.information(self, 'Saved', f'Project saved to {path}')


def main():
    app = QApplication(sys.argv)
    w = BuilderApp()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
