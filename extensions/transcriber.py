from .extensions import NewelleExtension
from .handlers import PromptDescription

class TranscribeExtension(NewelleExtension):

    id = "transcriber"
    name = "Audio Transcriber"

    def get_replace_codeblocks_langs(self) -> list:
        return ["transcribe"]

    def get_additional_prompts(self) -> list:
        return [
            PromptDescription("transcribe", "Transcribe Audio", "Transcribe audio files",
                "To transcribe audio files, use the following format:\n```transcribe\n/path/to/audio_file\n```"
            ),
        ]

    def get_answer(self, codeblock: str, lang: str) -> str | None:
        recognized = self.stt.recognize_file(codeblock)
        if recognized:
            return "Transcription result: " + recognized 
        else:
            return "Failed to recognize"
