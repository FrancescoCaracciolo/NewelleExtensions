from .utility.system import get_spawn_command
from .extensions import NewelleExtension
import subprocess


class ScreenshotExtension(NewelleExtension):
    name = "Screenshot"
    id = "screenshot"

    def get_additional_prompts(self) -> list:
        return [
            {
                "key": "screenshot",
                "setting_name": "screenshot",
                "title": "Take a screenshot",
                "description": "Take a screenshot",
                "default": True,
                "show_in_settings": True,
                "editable": True,
                "text": "You can take a screenshot of the user's screen using \n```take\nscreenshot\n```\nTake a screenshot every time the users ask for something that is on his screen or when he asks to do so.\nOnly take screenshots when it's necessary based on the user request.",
            }
        ]
    def get_replace_codeblocks_langs(self) -> list:
        return ["take"]

    def get_answer(self, codeblock: str, lang: str) -> str | None:
        cache_path = self.extension_path
        script = f"grim - | wl-copy && wl-paste > {cache_path}-$(date +%F_%T).png && echo {cache_path}-$(date +%F_%T).png"
        screenshot = subprocess.check_output(get_spawn_command() + ["bash", "-c", script])
        return "/attach_screenshot " + screenshot.decode("utf-8")

    def get_previous_user_message(self, start_id, history):
        for i in range(start_id, -1, -1):
            if history[i]["User"] == "User":
                return i

    def preprocess_history(self, history: list, prompts: list) -> tuple[list, list]:
        for i in range(len(history)):
            if history[i]["Message"].startswith(" /attach_screenshot"):
                screenshot_path = history[i]["Message"].replace(" /attach_screenshot ", "")
                prev_user = self.get_previous_user_message(i, history)
                history[i]["Message"] = screenshot_path
                if prev_user is not None:
                    history[prev_user]["Message"] = "```image\n" + screenshot_path + "```\n" + history[prev_user]["Message"]
                break
        return history, prompts
