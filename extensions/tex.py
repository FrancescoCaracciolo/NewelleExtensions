from gi.repository import Gio, Gtk
from .extensions import NewelleExtension
from .extra import find_module, install_module
import json
import os

class TexDisplay(NewelleExtension):
    id="tex"
    name="Display Latex"

    def __init__(self, pip_path: str, extension_path: str, settings):
        super().__init__(pip_path, extension_path, settings)
        self.cache = self.get_setting("cache", False)
        if self.cache is None:
            self.cache = {}
        else:
            self.cache = json.loads(self.cache)
        self.cachedir = os.path.join(self.extension_path, "tex")
        if not os.path.isdir(self.cachedir):
            os.makedirs(self.cachedir)

    def install(self):
        if not find_module("matplotlib"):
            install_module("matplotlib", self.pip_path)
        self.set_setting("cache", "{}")

    def get_replace_codeblocks_langs(self) -> list:
        return ["tex", "latex"]

    def get_extra_settings(self) -> list:
        return [
            {
                "key": "size",
                "title": "Equation Size",
                "description": "Size of the equations",
                "type": "range",
                "default": 100,
                "min": 50,
                "max": 300,
                "round-digits": 0
            }
        ]

    def get_additional_prompts(self) -> list:
        return [
            {
                "key": "latex",
                "setting_name": "latex",
                "title": "Latex support",
                "description": "Show latex equations",
                "editable": True,
                "show_in_settings": True,
                "default": True,
                "text": "Write mathematical expression in LaTeX format using the following format:\n```latex\nexpression\n```"
            }
        ]
    def get_gtk_widget(self, codeblock: str, lang: str) -> Gtk.Widget | None:
        codeblock = codeblock.replace("$", "")
        equations = codeblock.split("\n")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        size = self.get_setting("size")
        for equation in equations:
            equation = equation.replace("\\\\", "")
            scroll = Gtk.ScrolledWindow(propagate_natural_height=True, hexpand=True)
            scroll.set_child(self.render_latex(equation, int(size)))
            scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
            box.append(scroll)
        return box

    def render_latex(self, latex: str, size=150) -> Gtk.Image | Gtk.Picture:
       import matplotlib.pyplot as plt
       import uuid
       # Get text color
       widget = Gtk.Box()
       color = widget.get_style_context().lookup_color('window_fg_color')[1]
       
       # Check for cache
       id = latex + str(size) + str(color.red) + str(color.green) + str(color.blue)
       if id in self.cache:
           fname = self.cache[id]
       else: 
           # Create equation image
           plt.figure()
           plt.text(0.5, 0.5, r'$' + latex + r'$', fontsize=100, ha='center', color=(color.red, color.blue, color.green)) 
           plt.axis('off')
           # Get file name and save it in the cache
           fname = os.path.join(self.cachedir, uuid.uuid4().hex + '-symbolic.svg')
           self.cache[id] = fname
           self.update_cache()

           plt.tight_layout(pad=0)
           plt.savefig(fname, transparent=True, bbox_inches='tight', pad_inches=0)
       # Create Gtk.Picture
       img = Gtk.Picture()
       img.set_file(Gio.File.new_for_path(fname)) 
       img.set_size_request(-1, size)
       img.set_content_fit(Gtk.ContentFit.CONTAIN)
       #img.set_from_paintable(Gtk.IconPaintable.new_for_file(Gio.File.new_for_path('' + fname), size, 1))
       plt.close()
       return img

    def update_cache(self):
       self.set_setting("cache", json.dumps(self.cache))
