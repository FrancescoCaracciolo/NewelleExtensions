import json
import os
import threading
from .extensions import NewelleExtension
from .handlers import PromptDescription, ExtraSettings
from .tools import Tool, ToolResult


DEFAULT_UPDATE_PROMPT = (
    "You are a mood state analyst for a roleplay character. "
    "Based on the conversation provided, output a JSON object with updated mood values. "
    "Return ONLY valid JSON, no other text.\n\n"
    'Format: {"affection": <0-10>, "trust": <0-10>, "desire": <0-10>, "connection": <0-10>, '
    '"mood": <0-10>, "last_thought": "<short internal monologue>", '
    '"affection_description": "<1-2 words>", "trust_description": "<1-2 words>", '
    '"desire_description": "<1-2 words>", "connection_description": "<1-2 words>", '
    '"mood_description": "<1-2 words>"}\n\n'
    "Keep changes small and natural. Only include fields that changed. "
    "Values are on a 0-100 scale."
)

DEFAULT_MOOD_PROMPT = """[Character Mood State]
{CHARACTER_MOOD}"""

DEFAULT_STATE = {
    "affection": {"value": 50, "description": "Neutral"},
    "trust": {"value": 50, "description": "Neutral"},
    "desire": {"value": 10, "description": "None"},
    "connection": {"value": 50, "description": "Acquaintance"},
    "mood": {"value": 50, "description": "Neutral"},
    "last_thought": {"value": "Just met"},
    "message_count": 0,
}

VALUE_FIELDS = ["affection", "trust", "desire", "connection", "mood"]

BACKGROUND_HISTORY_LENGTH = 10


class CharacterTracker(NewelleExtension):
    name = "Character Mood Tracker"
    id = "character-mood-tracker"

    def __init__(self, pip_path, extension_path, settings):
        super().__init__(pip_path, extension_path, settings)
        self.state = {}
        self.session_message_count = 0
        self._update_in_progress = False
        self._load_state()

    # ── Persistence ──────────────────────────────────────────────

    def _get_state_file(self) -> str:
        cache_dir = os.path.join(self.extension_path, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, "mood_state.json")

    def _load_state(self):
        try:
            path = self._get_state_file()
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.state = json.load(f)
            else:
                self.state = dict(DEFAULT_STATE)
        except Exception:
            self.state = dict(DEFAULT_STATE)

        for dim in VALUE_FIELDS:
            val = self.get_setting(f"state_{dim}")
            if val is not None:
                self.state.setdefault(dim, {})["value"] = int(val)
        thought = self.get_setting("state_last_thought")
        if thought is not None:
            self.state["last_thought"] = {"value": str(thought)}

    def _save_state(self):
        try:
            for dim in VALUE_FIELDS:
                self.settings[f"state_{dim}"] = self.state.get(dim, {}).get("value", 50)
            lt = self.state.get("last_thought", {})
            self.settings["state_last_thought"] = lt.get("value", "") if isinstance(lt, dict) else str(lt)
            with open(self._get_state_file(), "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"CharacterTracker: error saving state: {e}")

    # ── Settings ─────────────────────────────────────────────────

    def get_extra_settings(self) -> list:
        settings = [
            ExtraSettings.ScaleSetting(
                "update_frequency",
                "Update frequency (messages)",
                "Automatically update mood every N user messages via background LLM call. 0 to disable.",
                10, 0, 100, 1,
            ),
            ExtraSettings.MultilineEntrySetting(
                "update_prompt",
                "Update prompt",
                "System prompt used for the background mood update LLM call.",
                DEFAULT_UPDATE_PROMPT,
            ),
            ExtraSettings.ToggleSetting("recall_model", "Recall Model after write operations", "Recall model after write operations", True),
        ]
        for dim in VALUE_FIELDS:
            default_val = DEFAULT_STATE.get(dim, {}).get("value", 50)
            settings.append(
                ExtraSettings.ScaleSetting(
                    f"state_{dim}",
                    dim.replace("_", " ").title(),
                    f"Manually set {dim.replace('_', ' ')} (0-100).",
                    default_val, 0, 100, 1,
                )
            )
        settings.append(
            ExtraSettings.MultilineEntrySetting(
                "state_last_thought",
                "Last Thought",
                "Manually edit the character's last internal monologue.",
                DEFAULT_STATE["last_thought"]["value"],
            )
        )
        return settings

    def _get_update_frequency(self) -> int:
        return int(self.get_setting("update_frequency") or 0)

    def _get_update_prompt(self) -> str:
        return self.get_setting("update_prompt") or DEFAULT_UPDATE_PROMPT

    # ── Tools ────────────────────────────────────────────────────

    def get_tools(self) -> list:
        return [
            Tool(
                name="read_mood_state",
                description="Read the current character mood state. Returns all tracked values.",
                func=self._tool_read_state,
                title="Read Mood State",
                tools_group="Character Mood",
                default_on=False,
            ),
            Tool(
                name="update_mood",
                description=(
                    "Update a single character mood dimension. Provide the dimension name "
                    "(affection, trust, desire, connection, mood), a new value (0-100), "
                    "and optionally a description of the state."
                ),
                func=self._tool_update_mood,
                title="Update Mood Value",
                tools_group="Character Mood",
            ),
            Tool(
                name="set_mood_state",
                description=(
                    "Batch-update multiple character mood values at once. Provide a 'changes' "
                    "dict with optional keys: affection, trust, desire, connection, mood "
                    "(integers 0-100), last_thought (string), and *_description (string) "
                    "for each dimension."
                ),
                func=self._tool_set_state,
                title="Set Mood State",
                tools_group="Character Mood",
                schema={
                    "type": "object",
                    "properties": {
                        "changes": {
                            "type": "object",
                            "properties": {
                                "affection": {"type": "integer"},
                                "trust": {"type": "integer"},
                                "desire": {"type": "integer"},
                                "connection": {"type": "integer"},
                                "mood": {"type": "integer"},
                                "last_thought": {"type": "string"},
                                "affection_description": {"type": "string"},
                                "trust_description": {"type": "string"},
                                "desire_description": {"type": "string"},
                                "connection_description": {"type": "string"},
                                "mood_description": {"type": "string"},
                            },
                        },
                    },
                    "required": ["changes"],
                },
            ),
        ]

    def _tool_read_state(self) -> ToolResult:
        result = ToolResult()
        result.set_output(self._format_state())
        return result

    def _tool_update_mood(self, dimension: str, value: int, description: str = "") -> ToolResult:
        result = ToolResult()
        dimension = dimension.strip().lower()

        if dimension == "last_thought":
            self.state["last_thought"] = {"value": str(value)}
            self._save_state()
            result.set_output(f"Updated last_thought to: {value}")
            return result

        if dimension not in VALUE_FIELDS:
            result.set_output(
                f"Error: unknown dimension '{dimension}'. "
                f"Valid dimensions: {', '.join(VALUE_FIELDS)}, last_thought"
            )
            return result

        clamped = max(0, min(100, int(value)))
        self.state[dimension]["value"] = clamped
        if description:
            self.state[dimension]["description"] = description
        self._save_state()
        if self.get_setting("recall_model"):
            result.set_output("Mood set")
        else:
            result.set_output(None)
        return result

    def _tool_set_state(self, changes: dict) -> ToolResult:
        result = ToolResult()
        applied = []

        for key, val in changes.items():
            if key in VALUE_FIELDS:
                clamped = max(0, min(100, int(val)))
                self.state[key]["value"] = clamped
                applied.append(f"{key}={clamped}")
            elif key == "last_thought":
                self.state["last_thought"] = {"value": str(val)}
                applied.append(f"last_thought=\"{val}\"")
            elif key.endswith("_description"):
                dim = key[: -len("_description")]
                if dim in VALUE_FIELDS:
                    self.state[dim]["description"] = str(val)
                    applied.append(f"{dim}_description=\"{val}\"")

        self._save_state()
        if applied:
            if self.get_setting("recall_model"):
                result.set_output("Updated mood state")
            else:
                result.set_output(None)
        else:
            result.set_output("No valid changes provided.")
        return result

    # ── Prompt ───────────────────────────────────────────────────

    def get_additional_prompts(self) -> list:
        return [
            PromptDescription(
                "character_tracker",
                "Character Mood Tracker",
                "Current emotional state of your character. Uses {CHARACTER_MOOD} placeholder.",
                DEFAULT_MOOD_PROMPT,
            ),
        ]

    # ── History preprocessing ────────────────────────────────────

    def preprocess_history(self, history: list, prompts: list) -> tuple[list, list]:
        state_text = self._format_state()

        # Replace placeholder in all prompts
        for i, prompt in enumerate(prompts):
            if "{CHARACTER_MOOD}" in prompt:
                prompts[i] = prompt.replace("{CHARACTER_MOOD}", state_text)

        # Automatic background update every N user messages
        freq = self._get_update_frequency()
        if freq > 0:
            user_msgs = sum(1 for h in history if h.get("User") == "User")
            if user_msgs > 0 and user_msgs % freq == 0 and not self._update_in_progress:
                recent = self._get_recent_messages(history)
                if recent:
                    self._update_in_progress = True
                    threading.Thread(
                        target=self._background_update,
                        args=(recent,),
                        daemon=True,
                    ).start()

        return history, prompts

    # ── Background LLM update ────────────────────────────────────

    def _get_recent_messages(self, history: list) -> list:
        """Extract recent User/Assistant messages for context."""
        filtered = [h for h in history if h.get("User") in ("User", "Assistant")]
        return filtered[-BACKGROUND_HISTORY_LENGTH:]

    def _background_update(self, recent_messages: list):
        """Call the LLM in background to assess and update mood state."""
        try:
            prompt = self._build_update_prompt(recent_messages)
            response = self.llm.generate_text(prompt)
            self._parse_and_apply_update(response)
        except Exception as e:
            print(f"CharacterTracker: background update failed: {e}")
        finally:
            self._update_in_progress = False

    def _build_update_prompt(self, recent_messages: list) -> str:
        """Build the LLM prompt with current state and conversation context."""
        parts = [self._get_update_prompt(), "\n\n"]

        parts.append("Current mood state:\n")
        for dim in VALUE_FIELDS:
            info = self.state.get(dim, {})
            val = info.get("value", 0)
            desc = info.get("description", "")
            parts.append(f"  {dim}: {val}/100 ({desc})\n")
        lt = self.state.get("last_thought", {})
        lt_val = lt.get("value", "") if isinstance(lt, dict) else str(lt)
        parts.append(f'  last_thought: "{lt_val}"\n')

        parts.append("\nRecent conversation:\n")
        for msg in recent_messages:
            role = msg.get("User", "Unknown")
            content = msg.get("Message", "")
            parts.append(f"{role}: {content}\n")

        parts.append("\nRespond with the updated mood JSON:")
        return "".join(parts)

    def _parse_and_apply_update(self, response: str):
        """Parse LLM JSON response and apply updates to state."""
        try:
            # Extract JSON from the response (may be wrapped in markdown codeblocks)
            text = response.strip()
            if text.startswith("```"):
                first_newline = text.find("\n")
                if first_newline != -1:
                    text = text[first_newline + 1 :]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            data = json.loads(text)

            applied = []
            for key, val in data.items():
                if key in VALUE_FIELDS:
                    clamped = max(0, min(100, int(val)))
                    self.state[key]["value"] = clamped
                    applied.append(key)
                elif key == "last_thought":
                    self.state["last_thought"] = {"value": str(val)}
                    applied.append("last_thought")
                elif key.endswith("_description"):
                    dim = key[: -len("_description")]
                    if dim in VALUE_FIELDS:
                        self.state[dim]["description"] = str(val)

            if applied:
                self._save_state()
                print(f"CharacterTracker: auto-updated: {', '.join(applied)}")
        except json.JSONDecodeError as e:
            print(f"CharacterTracker: failed to parse LLM response: {e}")
        except Exception as e:
            print(f"CharacterTracker: error applying update: {e}")

    # ── Helpers ──────────────────────────────────────────────────

    def _format_state(self) -> str:
        lines = []
        for dim in VALUE_FIELDS:
            info = self.state.get(dim, {})
            val = info.get("value", 0)
            desc = info.get("description", "")
            label = dim.replace("_", " ").title()
            lines.append(f"  {label}: {val}/100" + (f" — {desc}" if desc else ""))

        lt = self.state.get("last_thought", {})
        lt_val = lt.get("value", "") if isinstance(lt, dict) else str(lt)
        if lt_val:
            lines.append(f"  Last Thought: \"{lt_val}\"")

        return "Character Mood State:\n" + "\n".join(lines)
