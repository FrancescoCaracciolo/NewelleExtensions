# NewelleExtensions
Collection of my Newelle Extensions. Extensions are organized into the following folders:
- `llm/` – LLM provider extensions
- `tools/` – Tool extensions
- `tts/` – TTS extensions
- `legacy/` – Deprecated extensions

## Hyperbolic
Example of extension using `OpenAIHandler`. It adds the Hyperbolix.xyz support to Newelle.

[Extension file](https://github.com/FrancescoCaracciolo/NewelleExtensions/blob/main/llm/hyperbolic.py)

## PromptAdder
Extension that enables the user to add some custom prompts with custom names.

[Extension file](https://github.com/FrancescoCaracciolo/NewelleExtensions/blob/main/legacy/prompt_adder.py)

## Youtube Transcriptions
Add a tool to read youtube transcription from llm.

[Extension file](https://github.com/FrancescoCaracciolo/NewelleExtensions/blob/main/tools/youtube-transcription.py)

## TTS Speaker 
Example of Newelle mini-app. It allows you to use Newelle integrated TTS to read custom text.

[Extension file](https://github.com/FrancescoCaracciolo/NewelleExtensions/blob/main/tts/tts_speaker.py)


## Character Tracker

Adds tools to track character emotions and statistics in Newelle. 
It adds manual slider edit, both agentic way to update stats and periodic checks to update them via another LLM.

[Extension file](https://github.com/FrancescoCaracciolo/NewelleExtensions/blob/main/roleplay/character_tracker.py)



## Pollinations Image Generator
**Deprecated**, check the dedicated image generation extension.
Example of an extension that replaces codeblocks with GTK widgets with settings and custom dependencies support. It uses pollinations.ai to generate images.

[Extension file](https://github.com/FrancescoCaracciolo/NewelleExtensions/blob/main/legacy/pollinations.py)

## Perchance Image Generator
**Deprecated**, check the dedicated image generation extension.
Example of an extension that replaces codeblocks with GTK widgets. It uses perchance website to generate images. (~400MB download if you don't have playwright already)

[Extension file](https://github.com/FrancescoCaracciolo/NewelleExtensions/blob/main/legacy/perchance.py)


## Arch Wiki Integration
Example of an extension that replace codeblocks with responses to give to the LLM. It allows the model to search for Arch Wiki pages.

[Extension file](https://github.com/FrancescoCaracciolo/NewelleExtensions/blob/main/tools/arch.py)

There is also a more advanced integration with Tools, used in Nyarch Assistant. 

[Extension file](https://github.com/FrancescoCaracciolo/NewelleExtensions/blob/main/tools/arch_tools.py)
