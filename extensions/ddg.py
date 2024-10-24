from .extensions import NewelleExtension
from .llm import G4FHandler


class DDGExtension(NewelleExtension):
    name = "DuckDuckGo"
    id = "ddg"

    def get_llm_handlers(self) -> list[dict]:
        return [
            {
                "key": "ddg",
                "title": "DuckDuckGo",
                "description": "DuckDuckGo AI chat, private and fast",
                "class": DDGHandler
            }
        ]



class DDGHandler(G4FHandler):
    key = "ddg" 
    
    def __init__(self, settings, path):
        import g4f
        super().__init__(settings, path)
        self.client = g4f.client.Client(provider=g4f.Provider.DDG)        
    def get_extra_settings(self) -> list:
        return [
            {
                "key": "model",
                "title": _("Model"),
                "description": _("The model to use"),
                "type": "combo",
                "values": self.get_model(),
                "default": "gpt-4o-mini",
            }
        ] + super().get_extra_settings()

    def get_model(self):
        import g4f
        res = tuple()
        for model in g4f.Provider.DDG.models:
            res += ((model, model), )
        return res
