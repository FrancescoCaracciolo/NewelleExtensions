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
        plus = [
            {
                "key": "api",
                "title": _("API Key"),
                "description": _("API Key for Hyperbolic"),
                "type": "entry",
                "default": ""
            },
            {
                "key": "model",
                "title": _("Hyperbolic Model"),
                "description": _("Name of the Hyperbolic Model"),
                "type": "entry",
                "default": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                "website": "https://app.hyperbolic.xyz/models",
            }, 
        ]
        plus += [super().get_extra_settings()[3]]
        return plus
