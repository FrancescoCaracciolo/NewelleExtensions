from .extensions import NewelleExtension
from .llm import OpenAIHandler


class HyperbolicExtension(NewelleExtension):
    name = "Hyperbolic API"
    id = "hyperbolic"

    def get_llm_handlers(self) -> list[dict]:
        return [
            {
                "key": "hyperbolic",
                "title": "Hyperbolic.xyz",
                "description": "Hyperbolic LLM, provides some open source models",
                "class": HyperbolicHandler
            }
        ]

class HyperbolicHandler(OpenAIHandler):
    key = "hyperbolic"

    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://api.hyperbolic.xyz/v1/")
        self.set_setting("advanced_params", False)

    def get_extra_settings(self) -> list:
        return self.build_extra_settings("Hyperbolic", True, True, False, True, True, None, None, False, True)
