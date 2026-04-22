from openai._utils import is_sequence
from .extensions import NewelleExtension
from .handlers.llm import OpenAIHandler
from typing import Any, Callable 

class ChatAnyWhereExtension(NewelleExtension):
    name = "ChatAnyWhere"
    id = "chatanywhere"

    def get_llm_handlers(self) -> list[dict]:
        return [
            {
                "key": "chatanywhere",
                "title": "ChatAnyWhere",
                "description": "ChatAnyWhere API",
                "class": ChatAnyWhereHandler
            }
        ]

class ChatAnyWhereHandler(OpenAIHandler):
    key = "chatanywhere"

    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://api.chatanywhere.org/v1/")
        self.set_setting("advanced_params", False)

    def get_extra_settings(self) -> list:
        return self.build_extra_settings("ChatAnyWhere", True, True, False, True, True, None, None, False, True)

    def generate_text_stream(self, prompt: str, history: list[dict[str, str]] = [], system_prompt: list[str] = [], on_update: Callable[[str], Any] = lambda _: None, extra_args: list = []) -> str:
        from openai import OpenAI
        history.append({"User": "User", "Message": prompt})
        messages = self.convert_history(history, system_prompt)
        print([message["role"] for message in messages])
        api = self.get_setting("api")
        if api == "":
            api = "nokey"
        client = OpenAI(
            api_key=api,
            base_url=self.get_setting("endpoint")
        )
        top_p, temperature, max_tokens, presence_penalty, frequency_penalty = self.get_advanced_params()
        try:
            response = client.chat.completions.create(
                model=self.get_setting("model"),
                messages=messages,
                top_p=top_p,
                max_tokens=max_tokens,
                temperature=temperature,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty, 
                stream=True,
                extra_headers=self.get_extra_headers(),
                extra_body=self.get_extra_body(),
            )
            full_message = ""
            prev_message = ""
            is_reasoning = False
            for chunk in response:
                if len(chunk.choices) == 0:
                    continue
                if chunk.choices[0].delta.content:
                    if is_reasoning:
                        full_message += "</think>"
                        is_reasoning = False
                    full_message += chunk.choices[0].delta.content
                    args = (full_message.strip(), ) + tuple(extra_args)
                    if len(full_message) - len(prev_message) > 1:
                        on_update(*args)
                        prev_message = full_message
                elif hasattr(chunk.choices[0].delta, "reasoning") and chunk.choices[0].delta.reasoning is not None:
                    if not is_reasoning:
                        full_message += "<think>"
                    is_reasoning = True
                    full_message += chunk.choices[0].delta.reasoning
            return full_message.strip()
        except Exception as e:
            raise e
