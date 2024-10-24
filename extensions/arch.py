from .extra import install_module
from .extensions import NewelleExtension

class ArchWikiExtension(NewelleExtension):
    id = "archwiki"
    name = "Arch Wiki integration"

    def install(self):
        install_module("markdownify", self.pip_path)

    def get_replace_codeblocks_langs(self) -> list:
        return ["arch-wiki"]

    def get_additional_prompts(self) -> list:
        return [
            {
                "key": "archwiki",
                "setting_name": "archwiki",
                "title": "Arch Wiki",
                "description": "Enable Arch Wiki integration",
                "editable": True,
                "show_in_settings": True,
                "default": False,
                "text": "Use \n```arch-wiki\nterm\n```\nto search on Arch Wiki\nThen do not provide any other information. The user will give you the content of the page"
            }
        ]

    def get_answer(self, codeblock: str, lang: str) -> str | None:
        import requests
        import markdownify
        # Search for pages similar to that query in the wiki
        r = requests.get("https://wiki.archlinux.org/api.php", params={"search": codeblock, "limit": 1, "format": "json", "action": "opensearch"})
        if r.status_code != 200:
            return "Error contacting Arch API"
        # Pick the page
        page = r.json()[1][0]
        # Pick the page name in order to get its content
        name = page.split("/")[-1]
        r = requests.get("https://wiki.archlinux.org/api.php", params={"action": "parse", "page": name, "format": "json"})
        if r.status_code != 200:
            return "Error contacting Arch API"
        # Convert the HTML in Markdown in order to make it more readable for the LLM
        html = r.json()["parse"]["text"]["*"]
        return markdownify.markdownify(html)
