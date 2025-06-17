from .extensions import NewelleExtension
from gi.repository import GdkPixbuf, Gtk
from .utility.strings import quote_string
import subprocess, os
import json

class PerchanceExtension(NewelleExtension):
    name = "Perchance Image Generator"
    id = "perchanceimg"
    def __init__(self, a, b, c) -> None:
        super().__init__(a, b, c) 
        self.extension_cache = self.get_setting("cache")
        if self.extension_cache is None:
            self.extension_cache = {}
   
    def get_extra_settings(self):
        return [
            {
                "key": "positive-prompt",
                "title": "Positive Prompt",
                "description": "Positive Prompt to add to the request, you can specify with {prompt} the prompt given by the LLM",
                "type": "entry",
                "default": ""
            },
            {
                "key": "negative-prompt",
                "title": "Negative Prompt",
                "description": "Things you don't want in the image",
                "type": "entry",
                "default": ""
            },
            {
                "key": "style",
                "title": "Style",
                "description": "Style of the image",
                "type": "combo",
                "values": self.get_styles(),
                "default": "None"
            }
        ]

    def get_styles(self):
        styles = tuple()
        for style in STYLES.keys():
            styles += ( (style,style), )
        return styles

    @staticmethod
    def requires_sanbox_escape() -> bool:
        return True

    def install(self):
        bash_script = f"""
        cd {quote_string(self.extension_path)}
        mkdir perchanceapi
        cd perchanceapi
        git clone https://github.com/FrancescoCaracciolo/text-to-image-generator 
        cd text-to-image-generator
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt 
        playwright install
        """
        if not os.path.exists("perchanceapi"):
            subprocess.Popen(["flatpak-spawn", "--host", "bash", "-c", bash_script])     

    def get_replace_codeblocks_langs(self) -> list:
        return ["generateimage"]

    def get_additional_prompts(self) -> list:
        return [
            {
                "key": "generateimage",
                "setting_name": "generateimage",
                "title": "Generate Image",
                "description": "Generate images using Perchance AI",
                "editable": True,
                "show_in_settings": True,
                "default": True,
                "text": "- To generate images use: \n```generateimage\nprompt\n```. Use detailed prompts, with words separated by commas",
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
        style = self.get_setting("style")
        # Create a pixbuf loader that will load the image
        pixbuf_loader = GdkPixbuf.PixbufLoader()
        pixbuf_loader.connect("area-prepared", self.on_area_prepared, codeblock, spinner, image, box)
        # Generate the image and write it to the pixbuf loader
        os.chdir(self.extension_path)
        positive_prompt = self.get_setting("positive-prompt")
        negative_prompt = self.get_setting("negative-prompt")
        codeblock = positive_prompt.format(prompt=codeblock) if "{prompt}" in positive_prompt else codeblock + ", " + positive_prompt
        codeblock = STYLES[style]["prompt"].replace("[input.description]", codeblock)
        negative_prompt = STYLES[style]["negative"].replace("[input.negative]", negative_prompt)
        if codeblock in self.extension_cache:
            with open(self.extension_path + "/perchanceapi/text-to-image-generator/generated-pictures/" + self.extension_cache[codeblock], 'rb') as response:
                data = response.read()
                pixbuf_loader.write(data)
                pixbuf_loader.close()
            return
        try:
            fname = str(uuid.uuid4())
            bash_script = f"""
cd {quote_string(self.extension_path)}
cd perchanceapi/text-to-image-generator
source venv/bin/activate
python main.py -n 1 -f {fname} -p {quote_string(codeblock)} -np {quote_string(negative_prompt)} -r 512x512"""
            subprocess.check_output(["flatpak-spawn", "--host", "bash", "-c", bash_script])
            with open(self.extension_path + "/perchanceapi/text-to-image-generator/generated-pictures/" + fname + "1.jpeg", 'rb') as response:
                data = response.read()
                pixbuf_loader.write(data)
                pixbuf_loader.close()
            self.extension_cache[codeblock] = fname + "1.jpeg"
            self.set_setting("cache", self.extension_cache)
        except Exception as e:
            print("Exception generating the image: " + str(e))


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


# Styles list


STYLES = {
    "None": {
            "prompt": "[input.description]",
            "negative": "[input.negative]"
    },
    "Painted Anime Plus": {
        "prompt": "[input.description], anime, masterpiece, fine details, breathtaking artwork, painterly art style, high quality, 8k, very detailed, high resolution, exquisite composition and lighting, pretty anime character, adorable, featured on pixiv, very detailed, absolute masterpiece, sharp, realistic light, pastel, ((highlight)), (soft), (pretty), realistic background, realistic background light, ray-tracing, background, beautiful, (8k), realistic light, realistic light effect",
        "negative": "[input.negative], (worst quality, low quality, blurry:1.3), low-quality, deformed, text, poorly drawn, hilariously bad drawing, bad 3D render, ((line, outline)), face only, big head, Bad mouth, unnatural mouth, bad eyes, bad chin, unnatural chin",
        "meta:tags": "[({anime:100, painting:50, paintedAnime:50, drawing:55, cartoon:50})]"
    },
    "Painted Anime": {
        "prompt": "([/\b(male|man)\b/i.test(input.description) ? input.description.replace(/\b(male|man)\b/i, '(male, masculine, masc, male)') : input.description]), art by atey ghailan, painterly anime style at pixiv, art by kantoku, in art style of redjuice/necömi/rella/tiv pixiv collab, your name anime art style, masterpiece digital painting, exquisite lighting and composition, inspired by wlop art style, 8k, sharp, very detailed, high resolution, illustration ^2",
        "negative": "(worst quality, low quality, blurry:1.3), [input.negative], low-quality, deformed, text, poorly drawn[/\bmale\b/i.test(input.description) ? ', female, feminine, fem, female' : '']",
        "meta:tags": "[({anime:100, painting:100, paintedAnime:100, drawing:55, cartoon:50})]"
    },
    "3D Disney Character": {
        "prompt": "3D cartoon Disney character portrait render. [input.description], bokeh, 4k, highly detailed, Pixar render, CGI Animation, Disney, cute big circular reflective eyes, dof, (cinematic film), Disney realism, subtle details, breathtaking Pixar short, fine details, close up, sharp focus, HDR, Disney-style octane render, incredible composition, superb lighting and detail, [input.description]",
        "negative": "[input.negative], worst quality, poorly drawn, bad art, boring, deformed, bad composition, crappy artwork, bad lighting",
        "meta:tags": "[({disney:95, render:80, portrait:75, cartoon:90})]"
    },
    "2D Disney Character": {
        "prompt": "2D cartoon Disney character digital art of [input.description]. superb linework, classic 2D Disney style art, close-up, inspired by the art styles of Glen Keane and Aaron Blaise, Disney-style character concept with a Disney-style face, (trending on artstation), Disney-style version of [input.description]",
        "negative": "[input.negative], bad 3D render, bad 3D shadowing, worst quality, poorly drawn, low-resolution render, bad colors, a photo, terrible art, text, logo, bad composition, bad lighting, disfigured, deformed, bad anatomy"
    },
    "Professional Photo": {
        "prompt": "[input.description], {sharp|soft} focus, depth of field, 8k photo, HDR, professional lighting, taken with Canon EOS R5, 75mm lens",
        "negative": "[input.negative], worst quality, bad lighting, cropped, blurry, low-quality, deformed, text, poorly drawn, bad art, bad angle, boring",
        "meta:tags": "[({photo:95, portrait:60})]"
    },
    "Anime": {
        "prompt": "(anime art of [input.description]:1.2), masterpiece, 4k, best quality, anime art",
        "negative": "(worst quality, low quality:1.3), [input.negative], low-quality, deformed, text, poorly drawn",
    },
    "Drawn Anime": {
        "prompt": "digital art drawing, illustration of ([input.description]), anime drawing/art, bold linework, illustration, cel shaded, painterly style, digital art, masterpiece",
        "negative": "[input.negative], boring flat infographic, oversaturated, bad photo, terrible 3D render, bad anatomy"
    },
    "Cute Anime": {
        "prompt": "(((adorable, cute, kawaii)), [input.description], cute moe anime character portrait, adorable, featured on pixiv, kawaii moé masterpiece, cuteness overload, very detailed, sooooo adorable!!!, absolute masterpiece",
        "negative": "(worst quality, low quality:1.3), [input.negative], worst quality, ugly, 3D, photograph, bad art, blurry"
    },
    "Soft Anime": {
        "prompt": "[input.description], anime masterpiece, soft lighting, intricate, highly detailed, pixiv, anime art, 4k, art from your name anime, garden of words style art, high quality",
        "negative": "(worst quality, low quality:1.3), [input.negative], low-quality, deformed, text, poorly drawn"
    },
    "Mix Anime": {
        "prompt": "(anime art of [input.description]:1.2), masterpiece, 4k, best quality, anime art, very cute",
        "negative": "painterly anime artwork, [input.description], masterpiece, fine details, breathtaking artwork, painterly art style, high quality, 8k, very detailed, high resolution, exquisite composition and lighting[input.negative], (worst quality, low quality, blurry:1.3), black and white, low-quality, deformed, text, poorly drawn, bad art, bad anatomy, bad lighting"
    },
    "Fantasy Painting": {
        "prompt": "[input.description], d&d, fantasy, highly detailed, digital painting, artstation, sharp focus, fantasy art, illustration, 8k, in the style of greg rutkowski",
        "negative": "[input.negative], low-quality, deformed, text, poorly drawn"
    },
    "Fantasy Landscape": {
        "prompt": "[input.description], fantasy matte painting, absolute masterpiece, detailed matte painting by andreas rocha and greg rutkowski, by Brothers Hildebrandt, superb composition, vivid fantasy art, breathtaking fantasy masterpiece",
        "negative": "[input.negative], faded, blurry, bad art"
    },
    "Fantasy Portrait": {
        "prompt": "[input.description], d&d, fantasy, highly detailed, digital painting, artstation, sharp focus, fantasy art, character art, illustration, 8k, art by artgerm and greg rutkowski",
        "negative": "[input.negative], low-quality, deformed, text, poorly drawn"
    },
    "Studio Ghibli": {
        "prompt": "[input.description], (studio ghibli style art:1.3), sharp, very detailed, high resolution, inspired by hayao miyazaki, anime, art from ghibli movie",
        "negative": "(worst quality, low quality:1.3), [input.negative], low-quality, deformed, text, poorly drawn"
    },
    "50s Enamel Sign": {
        "prompt": "50s enamel sign of [input.description], 50s advert enamel sign, masterpiece, authentic vintage enamel sign",
        "negative": "[input.negative]"
    },
    "Vintage Comic": {
        "prompt": "comic book style art of [input.description], (drawing, by Dave Stevens, by Adam Hughes, 1940's, 1950's:1.2), hand-drawn, color, high resolution, best quality, closeup",
        "negative": "[input.negative], terrible photoshop, low contrast",
    },
    "3D Emoji": {
        "prompt": "masterpiece (([input.description])) cartoon emoji concept render, (close-up:1.3), facing forward, (matte), emoji render trending on artstation, noto color emoji, app icon, joypixels, simple design, new iOS 16.4 ((([input.description]))) emoji render, (simple background:1.2), (centered:1.2), masterpiece, telegram sticker, clash of clans character concept, (looking at camera), crisp render, sharp focus, simple cartoon design",
        "negative": "[input.negative], framed, inset, border, glare, blurry, out of focus, shiny"
    },
    "Illustration": {
        "prompt": "breathtaking illustration of [input.description], (illustration:1.3), masterpiece, breathtaking illustration",
        "negative": "[input.negative], low-quality, deformed, text, poorly drawn, bad 3D render",
        "meta:tags": "[({illustration:100, drawing:75})]"
    },
    "Flat Illustration": {
        "prompt": "[input.description], illustration, flat, 2D, vector art, masterpiece, made with adobe illustrator, behance competition winner, trending on dribble, 4k, high resolution, crisp lines",
        "negative": "[input.negative], bad art, children's crayon drawing, worst quality, blurry",
        "meta:tags": "[({illustration:85, drawing:40})]"
    },
    "3D Pokemon": {
        "prompt": "a pokemon creature, [input.description], [input.pokemonType ? input.pokemonType+', ' : '']4k render, beautiful pokemon digital art, fakemon, pokemon creature, cryptid, fakemon, masterpiece, {soft|sharp} focus, (best quality, high quality:1.3)",
        "negative": "[input.negative], distorted, deformed, bad art",
        "meta:tags": "[({pokemon:60})]"
    },
    "Painted Pokemon": {
        "prompt": "[input.description], [input.pokemonType ? input.pokemonType+', ' : '']4k digital painting of a pokemon, amazing pokemon art by piperdraws, cryptid creations by Piper Thibodeau, by Naoki Saito and {Tokiya|Mitsuhiro Arita}, incredible composition",
        "negative": "[input.negative], crappy 3D render",
        "meta:tags": "[({pokemon:50})]"
    },
    "2D Pokemon": {
        "prompt": "[input.description], [input.pokemonType ? input.pokemonType+', ' : '']pokemon creature concept, superb line art, beautiful pokemon digital art, fakemon, by Sowsow, pokemon creature, cryptid, fakemon, masterpiece, by Yuu Nishida, 4k",
        "negative": "[input.negative], distorted, deformed, bad art, low quality",
        "meta:tags": "[({pokemon:70, drawing:50, cartoon:35})]"
    },
   "MTG Card": {
        "prompt": "[input.description], Magic The Gathering",
        "negative": "[input.negative], low-quality, deformed, blurry, bad art"
    },
    "Realistic Images": {
        "prompt": "[input.description], high quality image, 4k, 8k, HD, UHD, Sharp Focus, In Frame",
        "negative": "[input.negative], low quality, deformed, blurry, bad art, drawing, painting, horrible resolutions, low DPI, low PPI, blurry, glitch, error",
        "meta": {"position": 5}
    },
    "Vintage Anime": {
        "prompt": "[input.description], vintage anime, 90's anime style, by hajime sorayama, by greg tocchini, anime masterpiece, pixiv, akira-style art, akira anime art, 4k, high quality",
        "negative": "[input.negative], (worst quality, low quality:1.3), bad art, distorted, deformed",
        "meta:tags": "({anime:40, vintage:50, drawing:50})"
    },
    "Neon Vintage Anime": {
        "prompt": "[input.description], ((neon vintage anime)) style, 90's anime style, hajime sorayama, greg tocchini, neon vintage anime masterpiece, anime art, 4k, high quality",
        "negative": "[input.negative], blurry, (worst quality, low quality:1.3), bad art, distorted, deformed",
        "meta:tags": "({anime:30, vintage:50})"
    },
    "Manga": {
        "prompt": "[input.description], incredible hand-drawn manga, black and white, by Takehiko Inoue, by Katsuhiro Otomo and akira toriyama manga, hand-drawn art by rumiko takahashi and Inio Asano, Ken Akamatsu manga art",
        "negative": "[input.negative], (worst quality, low quality:1.3), bad photo, bad 3D render, distorted, deformed, fuzzy, noisy, blurry, smudge",
        "meta:tags": "({anime:40, drawing:50, manga:100, comic:20, cartoon:30})"
    },
    "Fantasy World Map": {
        "prompt": "beautiful fantasy map of [input.description], beautiful fantasy map inspired by middle earth and azeroth and discworld and westeros and essos and the witcher world and tamriel and faerûn and thedas, 4k, beautiful colors, crisp, high-resolution artistic map, topographic 3D terrain, artistic map",
        "negative": "low quality, blurry, worst quality, childrens drawing, boring, logo, scratchy and grainy, messy, washed out colors, sepia, hazy",
        "meta:tags": "({map:90, fantasy:20})"
    },
    "Fantasy City Map": {
        "prompt": "an aerial view of a city, TTRPG city map showing the full city, [input.description], fantasy art, by senior environment artist, beautiful fantasy map",
        "negative": "fuzzy, bad art",
        "meta:tags": "({map:80, fantasy:20})"
    },
    "Old World Map": {
        "prompt": "fantasy world map of [input.description], fantasy world map, highly detailed digital painting, fantasy art, map illustration, 8k",
        "negative": "low resolution, worst quality",
        "meta:tags": "({map:70, fantasy:20})"
    },
    "Flat Style Icon": {
        "prompt": "[input.description], creative icon, flat style icon, masterpiece, high resolution, crisp, beautiful composition and color choice, beautiful flat painted style, behance contest-winner, award winning icon illustration, 8k, best quality",
        "negative": "gradient, bad design, blurry, jpeg compression artefacts, grainy, gradient, text, messy and inconsistent",
        "meta:tags": "({icon:80})"
    },
    "Flat Style Logo": {
        "prompt": "beautiful flat-style logo design depicting [input.description], creative flat-style logo design, trending on dribbble, featured on behance, portfolio piece, minimal flat design, breathtaking graphic design, 8k, high resolution vector logo, plain background, amazingly beautiful logo design, winner of best logo award",
        "negative": "photo, hilariously bad design, bad composition, bad colors, blurry, worst quality, low quality, shadow, boring, bad dsign, worst design ever, hilariously bad design, drop-shadow, gradient, messy, chaotic",
        "meta:tags": "({icon:80, logo:80})"
    },
    "Game Art Icon": {
        "prompt": "[input.description], a concept art icon for league of legends, a digital art logo, illustration, league of legends style icon, inspired by wlop style, 8k, dota 2 style icon, fine details, sharp, very detailed icon, high resolution rpg ability/spell/item icon",
        "negative": "low-quality, deformed, text, poorly drawn, multiple",
        "meta:tags": "({icon:70})"
    },
    "Waifu": {
        "prompt": "[input.description], waifu character portrait, art by Kazenoko, featured on pixiv, 1 girl, by Ilya Kuvshinov, Kantoku art, very detailed anime art by Redjuice",
        "negative": "(worst quality, low quality:1.3), [input.negative], bad photo, bad art, boring, bad 3D render, worst quality, ugly, blurry, low quality, poorly drawn, bad composition, deformed, bad 3D render, disfigured, bad anatomy, compression artifacts, dead, soulless, photorealistic",
        "meta:tags": "({anime:40, waifu:100, cartoon:20})"
    },
    "Traditional Japanese": {
        "prompt": "[input.description], in ukiyo-e art style, traditional japanese masterpiece",
        "negative": "blurry, low resolution, worst quality, fuzzy",
        "meta:tags": "({japanese:100, vintage:50, cartoon:30})"
    },
    "Nihonga Painting": {
        "prompt": "japanese nihonga painting about [input.description], Nihonga, ancient japanese painting, intricate, detailed",
        "negative": "[input.negative], framed blurry crappy photo, overly faded",
        "meta:tags": "({japanese:95, vintage:55, comic:70})"
    },
    "Painted Anime Plus Young": {
        "prompt": "[input.description], anime, masterpiece, fine details, breathtaking artwork, painterly art style, high quality, 8k, very detailed, high resolution, exquisite composition and lighting, pretty anime character, adorable, featured on pixiv, very detailed, absolute masterpiece, sharp, realistic light, pastel, ((highlight)), (soft), (pretty), realistic background, realistic background light, ray-tracing, background, beautiful, (8k), realistic light, realistic light effect, 18 years old, young, (small breasts:1.4), ((short)), ((short body)), cute, big head, (big eyes)",
        "negative": "[input.negative], (worst quality, low quality, blurry:1.3), low-quality, deformed, text, poorly drawn, hilariously bad drawing, bad 3D render, ((line, outline)), face only, big head, Bad mouth, unnatural mouth, bad eyes, bad chin, unnatural chin, Close up, Big boobs, (tall),(fat), close up",
        "meta:tags": "({})"
    },
    "Painted Anime Young": {
        "prompt": "([/\b(male|man)\b/i.test(input.description) ? input.description.replace(/\b(male|man)\b/i, '(male, masculine, masc, male)') : input.description]), art by atey ghailan, painterly anime style at pixiv, art by kantoku, in art style of redjuice/necömi/rella/tiv pixiv collab, your name anime art style, masterpiece digital painting, exquisite lighting and composition, inspired by wlop art style, 8k, sharp, very detailed, high resolution, illustration ^2, 18 years old, young, (small breasts:1.4), ((short)), ((short body)), cute, big head, (big eyes), narrow shoulders, small body, thin",
        "negative": "(worst quality, low quality, blurry:1.3), [input.negative], low-quality, deformed, text, poorly drawn[/\bmale\b/i.test(input.description) ? ', female, feminine, fem, female' : ''], Close up, Big boobs, (tall),(fat), close up",
        "meta:tags": "({})"
    },
    "Painted Anime Plus Younger": {
        "prompt": "[input.description], anime, masterpiece, fine details, breathtaking artwork, painterly art style, high quality, 8k, very detailed, high resolution, exquisite composition and lighting, pretty anime character, adorable, featured on pixiv, very detailed, absolute masterpiece, sharp, realistic light, pastel, ((highlight)), (soft), (pretty), realistic background, realistic background light, ray-tracing, background, beautiful, (8k), realistic light, realistic light effect, 18 years old, young, (small breasts:1.4), ((short)), ((short body)), cute, big head, (big eyes), adorable, cute moe anime, kawaii moé masterpiece, cuteness overload, (very short), Small physique, (big head), (short upper body)",
        "negative": "[input.negative], (worst quality, low quality, blurry:1.3), low-quality, deformed, text, poorly drawn, hilariously bad drawing, bad 3D render, ((line, outline)), face only, big head, Bad mouth, unnatural mouth, bad eyes, bad chin, unnatural chin, Close up, Big boobs, (tall),(fat), close up",
        "meta:tags": "({})"
    },
    "Painted Anime Younger": {
        "prompt": "([/\b(male|man)\b/i.test(input.description) ? input.description.replace(/\b(male|man)\b/i, '(male, masculine, masc, male)') : input.description]), art by atey ghailan, painterly anime style at pixiv, art by kantoku, in art style of redjuice/necömi/rella/tiv pixiv collab, your name anime art style, masterpiece digital painting, exquisite lighting and composition, inspired by wlop art style, 8k, sharp, very detailed, high resolution, illustration ^2, 18 years old, young, (small breasts:1.4), ((short)), ((short body)), cute, big head, (big eyes), narrow shoulders, small body, thin, adorable, cute moe anime, kawaii moé masterpiece, cuteness overload, (very short), Small physique, (big head), (short upper body)",
        "negative": "(worst quality, low quality, blurry:1.3), [input.negative], low-quality, deformed, text, poorly drawn[/\bmale\b/i.test(input.description) ? ', female, feminine, fem, female' : ''], Close up, Big boobs, (tall),(fat), close up",
        "meta:tags": "({})"
    },
    "Painted Anime Plus Youngest": {
        "prompt": "[input.description], anime, masterpiece, fine details, breathtaking artwork, painterly art style, high quality, 8k, very detailed, high resolution, exquisite composition and lighting, pretty anime character, adorable, featured on pixiv, very detailed, absolute masterpiece, sharp, realistic light, pastel, ((highlight)), (soft), (pretty), realistic background, realistic background light, ray-tracing, background, beautiful, (8k), realistic light, realistic light effect, 18 years old, young, (small breasts:1.4), (short:1.4), ((short body)), cute, big head, (big eyes), adorable, cute moe anime, kawaii moé masterpiece, cuteness overload, (very short), Small physique, (big head), (short upper body),(cute) slim (petite) ((tiny body and features, juvenile body)), ((adolescent)) ((very very young:1.3)) ((little))",
        "negative": "[input.negative], (worst quality, low quality, blurry:1.3), low-quality, deformed, text, poorly drawn, hilariously bad drawing, bad 3D render, ((line, outline)), face only, big head, Bad mouth, unnatural mouth, bad eyes, bad chin, unnatural chin, Close up, Big boobs, (tall),(fat), close up",
        "meta:tags": "({anime:100, painting:50, paintedAnime:50, drawing:55, cartoon:50, realistic:70})"
    },
    "Painted Anime Youngest": {
        "prompt": "([/\b(male|man)\b/i.test(input.description) ? input.description.replace(/\b(male|man)\b/i, '(male, masculine, masc, male)') : input.description]), art by atey ghailan, painterly anime style at pixiv, art by kantoku, in art style of redjuice/necömi/rella/tiv pixiv collab, your name anime art style, masterpiece digital painting, exquisite lighting and composition, inspired by wlop art style, 8k, sharp, very detailed, high resolution, illustration ^2, 18 years old, young, (small breasts:1.4), (short:1.4), ((short body)), cute, big head, (big eyes), narrow shoulders, small body, thin, adorable, cute moe anime, kawaii moé masterpiece, cuteness overload, (very short), Small physique, (big head), (short upper body),(cute) slim (petite) ((tiny body and features, juvenile body)), ((adolescent)) ((very very young:1.3)) ((little))",
        "negative": "(worst quality, low quality, blurry:1.3), [input.negative], low-quality, deformed, text, poorly drawn[/\bmale\b/i.test(input.description) ? ', female, feminine, fem, female' : ''], Close up, Big boobs, (tall),(fat), close up",
        "meta:tags": "({})"
        },
    "Realistic Humans": {
        "prompt": "[input.description], high quality image, 4k, 8k, HD, UHD",
        "negative": "[input.negative], low quality, deformed, blurry, bad art, drawing, painting, incorrect anatomy, ugliness, ugly, horrible resolutions, low DPI, low PPI, bad character positioning, absurd anatomy, tiling, pixelization, low pixel count, blurry, low-res face, low poly, Poorly Drawn Characters, Badly Drawn Eyes, Badly Drawn Mouth, Badly Drawn Ears, Badly Drawn Nose, Badly Drawn Hands, Badly Drawn Feet, Badly Drawn Legs, Badly Drawn Hair, Badly Drawn Clothing, bad anatomy, (ugly), missing arms, bad proportions, tiling, missing legs, blurry, (poorly drawn feet), morbid, cloned face, ((extra limbs)), (mutated hands), cropped, (disfigured), mutation, deformed, (mutilated), dehydrated, body out of frame, out of frame, (disfigured), ((bad anatomy)), (poorly drawn face), duplicate, cut off, (poorly drawn hands), error, low contrast, signature, (extra arms), underexposed, text, (extra fingers), overexposed, (too many fingers), (extra legs), bad art, ugly, (extra limbs), beginner, username, (fused fingers), amateur, watermark, (distorted face), worst quality, jpeg artifacts, low quality, (malformed limbs), long neck, low-res, (poorly Rendered face), low resolution, low saturation, (bad composition), Images cut out at the top, left, right, bottom, (deformed body features), (poorly rendered hands)",
        "modifiers": "[nsfwModifiers]",
        "meta": {"position": 6}
    },
    "𝗡𝗼 𝘀𝘁𝘆𝗹𝗲": {
        "prompt": "[input.description]",
        "negative": "[input.negative]",
        "meta": {"position": 7}
    },
    "Anti-NSFW": {
        "prompt": "[input.description], SFW",
        "negative": "[input.negative], NSFW, inappropriate, nudity, 18+ content",
        "meta": {"position": 8}
    },
    "League of Legends": {
        "prompt": "[input.description], fyptt.toconcept art, digital art, illustration, (league of legends style concept art), inspired by wlop style, 8k, fine details, sharp, very detailed, high resolution,anime, (realistic) ,magic the gathering, colorful background, no watermark,wallpaper, normal eyes",
        "negative": "[input.negative], low-quality, deformed, blurry, bad art, (watermark), (text), (bad eyes)",
        "meta": {"position": 9}
    },
    "Jester": {
        "prompt": "[input.description] (((jester laughing maniacally anime art style))) (((jester anime art style))) (((pointy jester hat anime art style))) (((yugioh anime art style))) (((neon colors))) (((vibrant colors))) (((bright colors))) (((lens flare))) (((light leaks))) (((long exposure)))",
        "negative": "[input.negative] (((yugioh hair))) (((low-quality))) (((deformed))) (((blurry))) (((bad art)))",
    },
    "Ninja": {
        "prompt": "[input.description], one character, ninja gaiden anime art style, ninja scroll anime art style, martial arts anime art style, 3D anime art style, heavy outlines art style, light leaks, lens flare, long exposure",
        "negative": "[input.negative], two or more characters, low-quality, deformed, blurry, bad art",
    },
    "Random Girl 1": {
        "prompt": "[input.description], one character, female in her late 20s, {dark|light|medium} skin complexion, smooth skin, american face, {dark|light|medium} {blue|green|gray|hazel|brown} eyes, pretty lips, pretty eyes, light makeup, abstract halftone background, thick border around image, vibrant colors, bright colors, high contrast, {amazingly beautiful|embodiment of perfection|stunningly gorgeous} girl anime art style",
        "negative": "[input.negative], more than one character, low-quality, deformed, blurry, bad art, muscular female, more than two arms, less than two arms, more than two hands, less than two hands, floating body parts, floating limbs, torso twisted backwards from legs, legs twisted backwards from torso, random legs that don't belong, random arms that don't belong, random limbs that don't belong, nipples in the wrong place, pale skin, leg in the wrong place, arm in the wrong place, knee bent the wrong way, deformed legs, flat nose, pointy nose, unnatural skin colors",
    },
    "Random Girl 2": {
        "prompt": "one character, female in her late 20s, {dark|light|medium} skin complexion, smooth skin, american face, {dark|light|medium} {blue|green|gray|hazel|brown} eyes, pretty lips, pretty eyes, light makeup, wearing {jeans|short shorts|a revealing outfit|a skin-tight bodysuit|a punk rock outfit|a steampunk outfit|a college cheerleader uniform|a skater girl outfit|a swimsuit|a bikini|underwear and a t-shirt|fancy underwear|a minidress with stockings|a miniskirt with stockings|leggings}, view from {the front|behind, rear projection}, {character portrait|{high-angle|low-angle|close up|over-the-shoulder|wide-angle|profile|full body|telephoto|panoramic|handheld} shot|pov shot}, abstract halftone background, thick border around image, vibrant colors, bright colors, high contrast, {amazingly beautiful|embodiment of perfection|stunningly gorgeous} girl anime art style",
        "negative": "[input.negative], more than one character, low-quality, deformed, blurry, bad art, muscular female, more than two arms, less than two arms, more than two hands, less than two hands, floating body parts, floating limbs, torso twisted backwards from legs, legs twisted backwards from torso, random legs that don't belong, random arms that don't belong, random limbs that don't belong, nipples in the wrong place, pale skin, leg in the wrong place, arm in the wrong place, knee bent the wrong way, deformed legs, flat nose, pointy nose, unnatural skin colors",
    },
    "Lego": {
        "prompt": "([input.description]), (legos art style:1.3), (lego video game art style:1.3)",
        "negative": "([input.negative]), low-quality, deformed, blurry, bad art",
    },
    "Skittles": {
        "prompt": "([input.description]), (skittles art style:1.3), (taste the rainbow art style:1.3), skittles, tropical skittles, sour skittles, neon color grading, bright color grading, vibrant color grading, light leaks, lens flare, long exposure",
        "negative": "([input.negative]), low-quality, deformed, blurry, bad art",
    },
    "Webcore": {
        "prompt": "([input.description]), (bold colors made in MS Paint and retro graphic design art style:1.3), (pixel art style:1.3), (neon color grading:1.2)",
        "negative": "([input.negative]), low-quality, deformed, blurry, bad art",
    },
    "Terraria": {
        "prompt": "([input.description]), (Terrarria Art Style:1.3), (Pixel Art Style:1.3), (Vibrant Color Grading:1.3)",
        "negative": "([input.negative]), low-quality, deformed, blurry, bad art",
    },
    "Final Fantasy": {
        "prompt": "([input.description]), (Final Fantasy Art Style:1.3), (CGI Video Game Art Style:1.3), (3D Video Game Art Style:1.3), (light leaks:1.1), (lens flare:1.1)",
        "negative": "([input.negative]), low-quality, deformed, blurry, bad art",
    },
    "Star Wars Character": {
        "prompt": "([input.description]), (((one character:1.5))),(Star Wars Art Style:1.3), (Animated Star Wars Art style:1.3), (Star Wars Anime Art style:1.3), (Anime Art style:1.3), (bright color grading:1.2), (vibrant color grading:1.2), (light leaks), (lens flare)",
        "negative": "([input.negative]), (((two or more characters:1.5))), (floating lightsabers:1.3), (unaccompanied lightsabers:1.3), low-quality, deformed, blurry, bad art",
    },
    "Star Wars Battle": {
        "prompt": "([input.description]), (((epic space battle:1.5))),(Star Wars Space Battle Art Style:1.3), (Animated Star Wars Art style:1.3), (Space Battle Anime Art style:1.3), (Anime Art style:1.3), (Starship Battle Art Style:1.3), (bright color grading:1.2), (vibrant color grading:1.2), (light leaks), (lens flare)",
        "negative": "([input.negative]), low-quality, deformed, blurry, bad art",
    },
    "Dragonball": {
        "prompt": "([input.description]), (Dragonball Anime Art Style:1.1), (YuGiOh art style:1.3), (bright color grading:1.2), (vibrant color grading:1.2), (light leaks), (lens flare)",
        "negative": "([input.negative]), (yugioh hair:1.5), low-quality, deformed, blurry, bad art",
    },
    "Undertale?": {
        "prompt": "([input.description]), (Undertale Anime Art Style:1.3)",
        "negative": "([input.negative]), low-quality, deformed, blurry, bad art",
    },
    "ENA": {
        "prompt": "([input.description]), (AND NEW GAME created by Peruvian animator Joel Guerra art style:1.3), (Surrealist crossed with Late 90s and Early 2000s Computer software and obscure console gaming imagery art style:1.3), (bright color grading:1.2)",
        "negative": "([input.negative]), low-quality, deformed, blurry, bad art",
    },
    "Neko (Catgirl)": {
        "prompt": "(((one character:1.5))), (human catgirl with a cat tail anime art style:1.3), (waifu anime art style:1.3), (gorgeous anime art style:1.3), (yugioh art style:1.3), (2d disney character art style:1.1), (catgirl anime art style:1.3), (neko anime art style:1.3), (vibrant color grading:1.6), (bright color grading:1.6), adult female catgirl, perfect body, {dark|light|medium} skin complexion, pretty lips, pretty eyes, light makeup, ({character portrait|{high-angle|low-angle|close up|over-the-shoulder|wide-angle|profile|full body|telephoto|panoramic|handheld} shot}:1.3)",
        "negative": "(((two or more characters:1.5))), (yugioh hair:1.5),low-quality, deformed, blurry, bad art, muscular female, more than two arms, less than two arms, more than two hands, less than two hands, floating body parts, floating limbs, unnatural female anatomy",
    },
    "American Girl": {
        "prompt": "(((one character:1.5))), (perfect gorgeous anime art style:1.3), (yugioh art style:1.3), (2d disney character art style:1.3), (gen13 comic art style), (stormwatch comic art style), tall adult female in her early 20s, perfect body, {dark|light|medium} skin complexion, smooth skin, american face, pretty lips, pretty eyes, light makeup, wearing {jeans|short shorts|a revealing outfit|a skin-tight bodysuit|a punk rock outfit|a steampunk outfit|a college cheerleader uniform|a skater girl outfit|a swimsuit|a bikini|underwear and a t-shirt with no bra|fancy underwear|a minidress with stockings|a miniskirt with stockings|leggings}:1.2, (view from {the front|behind}), ({character portrait|{high-angle|low-angle|close up|over-the-shoulder|wide-angle|profile|full body|telephoto|panoramic|handheld} shot}:1.3)",
        "negative": "(((two or more characters:1.5))), (pointy nose:1.5), (yugioh hair:1.5), low-quality, deformed, blurry",
    },
    "__NSFW - Realistic": {
        "prompt": "[input.description], highly realistic, realistic portrait, (nsfw), anatomically correct, realistic photograph, real colors, award winning photo, detailed face, realistic eyes, beautiful, sharp focus, high resolution, volumetric lighting, incredibly detailed, masterpiece, breathtaking, exquisite, great attention to skin and eyes",
        "modifiers": "[nsfwModifiers]",
        "negative": "[input.negative], unrealistic, animated, 3d, sketches, (text), low-quality, deformed, extra limbs, blurry, bad art, (logo), watermark, blurred, cut off, extra fingers, bad quality, distortion of proportions, deformed fingers, elongated body, cropped image, deformed hands, deformed legs, deformed face, twisted fingers, double image, long neck, extra limb, plastic, disfigured, mutation, sloppy, ugly, pixelated, bad hands, aliasing, overexposed, oversaturated, burnt image, fuzzy, poor quality, deformed arms",
    },
    "__NSFW - Anime": {
        "prompt": "[input.description], intricate detail, hyper-anime, trending on artstation, 8k, fluid motion, stunning shading, anime, highly detailed, realistic, (nsfw), dramatic lighting, beautiful, animation, sharp focus, award winning, masterpiece, cinematic, dynamic, cinematic lighting, breathtaking, exquisite, great attention to skin and eyes, exceptional, exemplary, unsurpassed, viral, popular, buzzworthy, up-and-coming, emerging, promising, acclaimed, premium",
        "negative": "[input.negative], photography, low-quality, deformed, (text), blurry, bad art, (logo), watermark, blurred, cut off, extra fingers, bad quality, distortion of proportions, deformed fingers, elongated body, cropped image, deformed hands, deformed legs, deformed face, twisted fingers, double image, long neck, extra limb, plastic, disfigured, mutation, sloppy, ugly, pixelated, bad hands, aliasing, overexposed, oversaturated, burnt image, fuzzy, poor quality, extra limbs, deformed arms, Mosaic",
        "modifiers": "[animeModifiers]"
    },
    "__NSFW - Realistic (Stronger)": {
        "prompt": "[input.description], highly realistic, realistic portrait, (((nsfw))), anatomically correct, realistic photograph, real colors, award winning photo, detailed face, realistic eyes, beautiful, sharp focus, high resolution, volumetric lighting, incredibly detailed, masterpiece, breathtaking, exquisite, great attention to skin and eyes",
        "modifiers": "[nsfwModifiers]",
        "negative": "[input.negative], unrealistic, animated, sketches, (text), low-quality, deformed, extra limbs, blurry, bad art, (logo), watermark, blurred, cut off, extra fingers, bad quality, distortion of proportions, deformed fingers, elongated body, cropped image, deformed hands, deformed legs, deformed face, twisted fingers, double image, long neck, extra limb, plastic, disfigured, mutation, sloppy, ugly, pixelated, bad hands, aliasing, overexposed, oversaturated, burnt image, fuzzy, poor quality, deformed arms",
    },
    "__NSFW - Anime (Stronger)": {
        "prompt": "[input.description], intricate detail, hyper-anime, trending on artstation, 8k, fluid motion, stunning shading, anime, highly detailed, realistic, (((nsfw))), dramatic lighting, beautiful, animation, sharp focus, award winning, masterpiece, cinematic, dynamic, cinematic lighting, breathtaking, exquisite, great attention to skin and eyes, exceptional, exemplary, unsurpassed, viral, popular, buzzworthy, up-and-coming, emerging, promising, acclaimed, premium",
        "modifiers": "[animeModifiers]",
        "negative": "[input.negative], photography, low-quality, deformed, (text), blurry, bad art, (logo), watermark, blurred, cut off, extra fingers, bad quality, distortion of proportions, deformed fingers, elongated body, cropped image, deformed hands, deformed legs, deformed face, twisted fingers, double image, long neck, extra limb, plastic, disfigured, mutation, sloppy, ugly, pixelated, bad hands, aliasing, overexposed, oversaturated, burnt image, fuzzy, poor quality, extra limbs, deformed arms, Mosaic",
    },
    "NSFW Painted Anime": {
        "prompt": "[/\b(male|man)\b/i.test(input.description) ? input.description.replace(/\b(male|man)\b/i, '(male, masculine, masc, male)') : input.description], art by atey ghailan, painterly anime style at pixiv, art by kantoku, in art style of redjuice/necömi/rella/tiv pixiv collab, your name anime art style, masterpiece digital painting, exquisite lighting and composition, inspired by wlop art style, 8k, sharp, very detailed, high resolution, illustration ^2",
        "prompt_alt": "painterly anime artwork, [input.description], masterpiece, fine details, breathtaking artwork, painterly art style, high quality, 8k, very detailed, high resolution, exquisite composition and lighting, ((NSFW))",
        "negative": "(worst quality, low quality, blurry:1.3), [input.negative], low-quality, deformed, text, poorly drawn[/\bmale\b/i.test(input.description) ? ', female, feminine, fem, female' : ''], (worst quality, low quality, blurry:1.3), black and white, low-quality, deformed, text, poorly drawn, bad art, bad anatomy, bad lighting, disfigured, faded, blurred face",
        "meta": {"tags": "[({anime:100, painting:100, paintedAnime:100, drawing:55, cartoon:50})]"},
        "modifiers": "[animeModifiers]",
    },
    "Realistic Human Generator": {
        "prompt": "[input.description], in soft gaze, looking straight at the camera, skin blemishes, imperfect skin, skin pores, no makeup, no cosmetics, matured, solo, centered, RAW photo, detailed, clear features, sharp focus, film grain, 8k uhd, candid portrait, natural lighting",
        "negative": "[input.negative], (wrong sex, wrong gender, wrong age, perfect skin, facial hair on women: 1.1), (black and white, monochrome, highly saturated, overexposure:1.1), (cropped, collage, multiple people:1.1), (famous people, models, artists, celebrities), makeup, cosmetics, denim, gore, blood, camera, deviantart, artstation, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime, illustration, painting, cross eyes, have strabismus, hands, jpeg",
    },
}
