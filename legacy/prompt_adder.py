from .extensions import NewelleExtension
from .handlers import ExtraSettings, PromptDescription


class PromptAdderExtensiion(NewelleExtension):
    id = "pormptadder"
    name = "Prompt Adder"

    def __init__(self, pip_path: str, extension_path: str, settings):
        super().__init__(pip_path, extension_path, settings)

    def get_extra_settings(self) -> list:
        return [
            ExtraSettings.ScaleSetting(
                "prompts", "Prompts number", "Number of prompts to add", 1, 0, 10, 0
            ),
            ExtraSettings.NestedSetting("prompts", "Prompts titles", "Change the title of added prompts, you can edit the prompts in the settings", [
                ExtraSettings.MultilineEntrySetting("promptadder" + str(i), "Prompt " + str(i), "Change the title of prompt " + str(i), "Prompt " + str(i))
                for i in range(10)
            ])
        ]

    def get_prompt_name(self, i):
        return self.get_setting("promptadder" + str(i))

    def get_additional_prompts(self) -> list:
        return [
            PromptDescription("promptadder" + str(i), self.get_prompt_name(i), "Prompt added by PromptAdder extension", "")
            for i in range(int(self.get_setting("prompts")))
        ]
