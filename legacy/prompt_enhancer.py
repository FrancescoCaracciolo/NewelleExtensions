from .extensions import NewelleExtension


class PromptEnhancer(NewelleExtension):
    id = "promptenhancer"
    name = "Prompt Enhancer"

    def get_prompt(self):
        DEFAULT_PROMPT = """1. **Analyze Context:** Review the entire chat history to extract key themes, user intent, and relevant details.  
2. **Extract Essential Instructions:** Identify and isolate the core prompts, tool descriptions, and behavioral guidelines from the original list.  
3. **Eliminate Redundancies:** Remove any outdated, repetitive, or unnecessary parts of the original prompts.  
4. **Organize Structure:** Rearrange the remaining instructions into a clear, logical sequence that flows naturally.  
5. **Plan Tool Integration:** Develop a step-by-step strategy for when and how to use each tool, ensuring they support the intended outcomes.  
6. **Synthesize Final Prompt:** Combine the refined instructions and tool usage plan into a concise, coherent prompt that effectively guides the conversation.
        """
        return

    def get_additional_prompts(self) -> list:
        return [
            {
                "key": "enhance",
                "setting_name": "enhance",
                "title": "Prompt Enhancer",
                "description": "NOTE: This prompt must start with PROMPTENHANCER:\nBy disabling this prompt, you disable the prompt enhancer",
                "default": True,
                "show_in_settings": True,
                "editable": True,
                "text": self.get_prompt()
            }
        ]

    def preprocess_history(self, history: list, prompts: list) -> tuple[list, list]:
        for prompt in prompts:
            if prompt.startswith("PROMPTENHANCER:"):
                prompt = prompt.replace("PROMPTENHANCER:", "")
                
                for i in range(len(history)):
                    if history[i]["User"] == "User":
                        history[i]["Message"] = prompt
                        break
        return history, prompts
