from .extensions import NewelleExtension
from .llm import OpenAIHandler
import requests
from gi.repository import GdkPixbuf, Gtk

class ClashAIExtension(NewelleExtension):
    key = "clashai"
    id = "clashai"
    name = "ClashAI"

    def get_extra_settings(self) -> list:
        return [
            {
                "key": "model",
                "title": "Image Model",
                "description": "Select the model to use",
                "type": "entry",
                "default": "imagen-3.0-generate-001",
            },
            {
                "key": "size",
                "title": "Image Size",
                "description": "Select the size to use",
                "type": "entry",
                "default": "256x256",
            }
        ] 
   
    def get_additional_prompts(self) -> list:
        return [
            {
                "key": "generate-image",
                "setting_name": "generate-image",
                "title": "Generate Image",
                "description": "Generate images using ClashAI",
                "editable": True,
                "show_in_settings": True,
                "default": True,
                "text": "You can generate images using: \n```generate-image\nprompt\n```. Use detailed prompts, with words separated by commas",
            }
        ]
    def get_llm_handlers(self) -> list[dict]:
        return [{
            "key": "clashai",
            "title": "ClashAI",
            "description": "ClashAI LLM handler",
            "class": ClashAIHandler
        }]

    def get_replace_codeblocks_langs(self) -> list:
        return ["generate-image"]
    
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
        import requests
        # Create a pixbuf loader that will load the image
        pixbuf_loader = GdkPixbuf.PixbufLoader()
        pixbuf_loader.connect("area-prepared", self.on_area_prepared, spinner, image, box)
        # Generate the image and write it to the pixbuf loader
        client = ClashAIHandler(self.settings, self.path).get_client()

        response = client.images.generate(
            prompt=codeblock,
            n=1,
            model=self.get_setting("model"),
            size=self.get_setting("size"),
        )
        url = response.data[0].url
        try:
            response = requests.get(url, stream=True) #stream = True prevent download the whole file into RAM
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192): #Load in chunks to avoid consuming too much memory for large files
                pixbuf_loader.write(chunk)
        except Exception as e:
            print("Exception generating the image: " + str(e))

    def on_area_prepared(self, loader: GdkPixbuf.PixbufLoader, spinner: Gtk.Spinner, image: Gtk.Image, box: Gtk.Box):
        # Function runs when the image loaded. Remove the spinner and open the image
        image.set_from_pixbuf(loader.get_pixbuf())
        box.remove(spinner)
        box.append(image)


class ClashAIHandler(OpenAIHandler):
    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://api.clashai.eu/v1")

    def supports_vision(self) -> bool:
        return True

    def get_extra_settings(self) -> list:
        return self.build_extra_settings("ClashAI", True, True, False, True, True, None, None, False, True)

    def get_client(self):
        from openai import Client
        return Client(api_key=self.get_setting("api"), base_url=self.get_setting("endpoint"))

