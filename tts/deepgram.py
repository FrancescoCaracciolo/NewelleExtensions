from .extensions import NewelleExtension
from .handlers import ErrorSeverity, HandlerDescription, ExtraSettings
from .handlers.tts import TTSHandler
from .utility.pip import install_module, find_module


class Deepgram(NewelleExtension):
    id = "deepgram"
    name = "Deepgram"
    
    def get_tts_handlers(self) -> list[dict]:
        return [
            HandlerDescription(
                key="deepgram",
                handler_class=DeepgramHandler,
                title="Deepgram",
                description="Deepgram TTS",
            )
        ]
    

class DeepgramHandler(TTSHandler):
    key = "deepgram"
    def install(self):
        install_module("deepgram-sdk", self.pip_path)

    def is_installed(self):
        return find_module("deepgram") is not None

    def get_extra_settings(self) -> list:
        return super().get_extra_settings() + [
            ExtraSettings.EntrySetting("api", _("API Key"), _("The API key to use"), "", password=True), 
        ]
    
    def get_voices(self):
        aura2_en = [
            "aura-2-amalthea-en", "aura-2-andromeda-en", "aura-2-apollo-en", 
            "aura-2-arcas-en", "aura-2-aries-en", "aura-2-asteria-en", 
            "aura-2-athena-en", "aura-2-atlas-en", "aura-2-aurora-en", 
            "aura-2-callista-en", "aura-2-cora-en", "aura-2-cordelia-en", 
            "aura-2-delia-en", "aura-2-draco-en", "aura-2-electra-en", 
            "aura-2-harmonia-en", "aura-2-helena-en", "aura-2-hera-en", 
            "aura-2-hermes-en", "aura-2-hyperion-en", "aura-2-iris-en", 
            "aura-2-janus-en", "aura-2-juno-en", "aura-2-jupiter-en", 
            "aura-2-luna-en", "aura-2-mars-en", "aura-2-minerva-en", 
            "aura-2-neptune-en", "aura-2-odysseus-en", "aura-2-ophelia-en", 
            "aura-2-orion-en", "aura-2-orpheus-en", "aura-2-pandora-en", 
            "aura-2-phoebe-en", "aura-2-pluto-en", "aura-2-saturn-en", 
            "aura-2-selene-en", "aura-2-thalia-en", "aura-2-theia-en", 
            "aura-2-vesta-en", "aura-2-zeus-en"
        ]
        aura2_es = [
            "aura-2-sirio-es", "aura-2-nestor-es", "aura-2-carina-es", 
            "aura-2-celeste-es", "aura-2-alvaro-es", "aura-2-diana-es", 
            "aura-2-aquila-es", "aura-2-selena-es", "aura-2-estrella-es", 
            "aura-2-javier-es"
        ]
        aura1_en = [
            "aura-asteria-en", "aura-luna-en", "aura-stella-en", 
            "aura-athena-en", "aura-hera-en", "aura-orion-en", 
            "aura-arcas-en", "aura-perseus-en", "aura-angus-en", 
            "aura-orpheus-en", "aura-helios-en", "aura-zeus-en"
        ]
        voices = tuple()
        for voice in (aura2_en + aura2_es + aura1_en):
            voices += ((voice, voice), )
        return voices
    
    def save_audio(self, message, file):
        from deepgram import (
            DeepgramClient,
            SpeakOptions,
        )
        message = {"text": message}
        try:
            # STEP 1 Create a Deepgram client using the API key from environment variables
            deepgram = DeepgramClient(api_key=self.get_setting("api"))

            # STEP 2 Call the save method on the speak property
            options = SpeakOptions(
                model=self.get_current_voice(),
            )

            response = deepgram.speak.rest.v("1").save(file, message, options)
            print(response.to_json(ident=4))
        except Exception as e:
            print(f"Error connecting to Deepgram: {e}")
            self.throw("Error connecting to Deepgram", ErrorSeverity.WARNING)
