from .extensions import NewelleExtension
from gi.repository import GdkPixbuf, Gtk

class PollinationsExtension(NewelleExtension):
    name = "Pollinations Image Generator"
    id = "pollinationsimg"
    def get_replace_codeblocks_langs(self) -> list:
        return ["generate-image"]

    def get_additional_prompts(self) -> list:
        return [
            {
                "key": "generate-image",
                "setting_name": "generate-image",
                "title": "Generate Image",
                "description": "Generate images using Pollinations AI",
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
        # Add the image to the box
        box.append(image)

        # Create the thread that will load the image in background
        thread = Thread(target=self.generate_image, args=(codeblock, image, spinner, box))
        # Start the thread
        thread.start()
        # Return the box
        return box

    def generate_image(self, codeblock, image: Gtk.Image, spinner: Gtk.Spinner, box: Gtk.Box):
        import urllib.request
        import urllib.parse
        # Create a pixbuf loader that will load the image
        pixbuf_loader = GdkPixbuf.PixbufLoader()
        pixbuf_loader.connect("area-prepared", self.on_area_prepared, spinner, image, box)
        # Generate the image and write it to the pixbuf loader
        try:
            url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(codeblock)
            with urllib.request.urlopen(url) as response:
                data = response.read()
                pixbuf_loader.write(data)
                pixbuf_loader.close()
        except Exception as e:
            print("Exception generating the image: " + str(e))

    def on_area_prepared(self, loader: GdkPixbuf.PixbufLoader, spinner: Gtk.Spinner, image: Gtk.Image, box: Gtk.Box):
        # Function runs when the image loaded. Remove the spinner and open the image
        image.set_from_pixbuf(loader.get_pixbuf())
        box.remove(spinner)
        box.append(image)
