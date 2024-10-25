from .extensions import NewelleExtension
from gi.repository import GdkPixbuf, Gtk
from .extra import quote_string
import subprocess, os
import json

class PerchanceExtension(NewelleExtension):
    name = "Perchance Image Generator"
    id = "perchanceimg"
    positive_prompt = ""
    negative_prompt = ""
    def __init__(self, a, b, c) -> None:
        super().__init__(a, b, c) 
        self.cachefile = os.path.join(self.extension_path, "perchanceimg.json")
        if not os.path.isdir(self.extension_path):
            os.makedirs(self.extension_path)

        if not os.path.exists(self.cachefile):
            with open(self.cachefile, "w+") as f:
                f.write("{}")
        
        self.extension_cache = json.load(open(self.cachefile, "r")) 

    def save_cache(self):
        with open(self.cachefile, "w") as f:
            json.dump(self.extension_cache, f)
    
    def install(self):
        bash_script = """
        mkdir perchanceapi
        cd perchanceapi
        git clone https://github.com/lsimek/perchance-image-generator.git 
        cd perchance-image-generator
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt 
        playwright install
        """
        old_cwd = os.getcwd()
        os.chdir(self.extension_path)
        if not os.path.exists("perchanceapi"):
            subprocess.Popen(["flatpak-spawn", "--host", "bash", "-c", bash_script])
        
        os.chdir(old_cwd) 
    def get_replace_codeblocks_langs(self) -> list:
        return ["generate-image"]

    def get_additional_prompts(self) -> list:
        return [
            {
                "key": "generate-image",
                "setting_name": "generate-image",
                "title": "Generate Image",
                "description": "Generate images using Perchance AI",
                "editable": True,
                "show_in_settings": True,
                "default": True,
                "text": "You can generate images using: \n```generate-image\nprompt\n```. Use detailed prompts, with words separated by commas",
            }
        ]

    def get_gtk_widget(self, codeblock: str, lang: str) -> Gtk.Widget | None:
        from threading import Thread
        # Create the box that will be returned
        box = Gtk.Box()
        # Create a spinner while loading the image 
        spinner = Gtk.Spinner(spinning=True)
        # Add the spinner to the box
        box.append(spinner)
        # Create the image widget that will replace the spinner 
        image = Gtk.Image()
        image.set_size_request(400, 400)

        # Create the thread that will load the image in background
        thread = Thread(target=self.generate_image, args=(codeblock, image, spinner, box))
        # Start the thread
        thread.start()
        # Return the box
        return box

    def generate_image(self, codeblock, image: Gtk.Image, spinner: Gtk.Spinner, box: Gtk.Box):
        import uuid
        # Create a pixbuf loader that will load the image
        pixbuf_loader = GdkPixbuf.PixbufLoader()
        pixbuf_loader.connect("area-prepared", self.on_area_prepared, codeblock, spinner, image, box)
        # Generate the image and write it to the pixbuf loader
        old_cwd = os.getcwd()
        os.chdir(self.extension_path)
        codeblock = self.positive_prompt.format(prompt=codeblock)
        if codeblock in self.extension_cache:
            with open("perchanceapi/perchance-image-generator/generated-pictures/" + self.extension_cache[codeblock], 'rb') as response:
                data = response.read()
                pixbuf_loader.write(data)
                pixbuf_loader.close()
            os.chdir(old_cwd)
            return
        try:
            fname = str(uuid.uuid4())
            bash_script = f"""
cd perchanceapi/perchance-image-generator
source venv/bin/activate
python main.py -n 1 -f {fname} -p {quote_string(codeblock)} -np {quote_string(self.negative_prompt)} -r 512x512"""
            subprocess.check_output(["flatpak-spawn", "--host", "bash", "-c", bash_script])
            with open("perchanceapi/perchance-image-generator/generated-pictures/" + fname + "1.jpeg", 'rb') as response:
                data = response.read()
                pixbuf_loader.write(data)
                pixbuf_loader.close()
            self.extension_cache[codeblock] = fname + "1.jpeg"
            self.save_cache()
        except Exception as e:
            print("Exception generating the image: " + str(e))
        os.chdir(old_cwd)


    def on_area_prepared(self, loader: GdkPixbuf.PixbufLoader, prompt, spinner: Gtk.Spinner, image: Gtk.Image, box: Gtk.Box):
        # Function runs when the image loaded. Remove the spinner and open the image
        image.set_from_pixbuf(loader.get_pixbuf())
        box.remove(spinner)
        b2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        exp = Gtk.Expander(label="prompt")
        b2.append(image)
        b2.append(exp)
        exp.set_child(Gtk.Label(label=prompt, wrap=True))
        box.append(b2)
