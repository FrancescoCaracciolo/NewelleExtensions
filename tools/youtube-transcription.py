from .extensions import NewelleExtension
from .handlers import PromptDescription, ErrorSeverity, ExtraSettings
from .utility.pip import install_module, find_module

class YoutubeTranscriber(NewelleExtension):
    id = "youtubetranscriber"
    name = "Youtube Transcriber"


    def install(self):
        install_module("youtube-transcript-api", self.pip_path)

    def is_installed(self) -> bool:
        return find_module("youtube_transcript_api") is not None

    def get_extra_settings(self) -> list:
        return [
            ExtraSettings.EntrySetting("languages", "Languages", "Comma-separated list of languages for transcriptions", "en,cn"),
            ExtraSettings.ButtonSetting("update", "Update Youtube Trancriber", "Update Youtube Transcriber python version to latest, might fix some issues", lambda x: self.install(), "Update"),
        ]
    def get_additional_prompts(self) -> list:
        return [PromptDescription(
            key="youtubetranscriber",
            title="Transcribe youtube videos",
            description="Transcribe youtube videos",
            text="- To transcribe youtube videos, use:\n```youtube\nurl\n```",
        )] 
    
    def get_replace_codeblocks_langs(self) -> list:
        return ["youtube"]

    def get_answer(self, codeblock: str, lang: str) -> str | None:
        from youtube_transcript_api import YouTubeTranscriptApi
        languages = self.get_setting("languages").split(",")
        video_id = self.video_id(codeblock)
        if video_id is None:
            return "Failed to get the video"
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript = ytt_api.fetch(video_id, languages=languages)
        except Exception as e:
            return "Could not transcribe video: " + str(e)
        return " ".join([t.text for t in transcript])

    @staticmethod
    def video_id(value):
        from urllib.parse import urlparse, parse_qs
        query = urlparse(value)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        return None

