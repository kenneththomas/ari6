from __future__ import annotations

import datetime
import json
import os
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from threading import RLock
from typing import Iterable


PERSONA_KEY_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DEFAULT_PERSONA_KEY = "ari"


@dataclass(frozen=True)
class Persona:
    key: str
    display_name: str
    avatar_url: str
    prompt: str
    use_bot_identity: bool = False

    def webhook_kwargs(self) -> dict[str, str]:
        kwargs = {"username": self.display_name}
        if self.avatar_url:
            kwargs["avatar_url"] = self.avatar_url
        return kwargs

    @classmethod
    def from_dict(cls, data: dict) -> "Persona":
        return cls(
            key=str(data.get("key", "")).strip().lower(),
            display_name=str(data.get("display_name", "")).strip(),
            avatar_url=str(data.get("avatar_url", "")).strip(),
            prompt=str(data.get("prompt", "")).strip(),
            use_bot_identity=bool(data.get("use_bot_identity", False)),
        )


def normalize_persona_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if not key or not PERSONA_KEY_PATTERN.fullmatch(key):
        raise ValueError("Persona keys must contain letters or numbers")
    return key


class PersonaStore:
    """Merge public built-ins with persistent, deployment-local overrides."""

    def __init__(self, builtins_path: Path | str, state_path: Path | str):
        self.builtins_path = Path(builtins_path)
        self.state_path = Path(state_path)
        self._lock = RLock()
        self._shared_prompt = ""
        self._builtins: dict[str, Persona] = {}
        self._overrides: dict[str, Persona] = {}
        self._deleted: set[str] = set()
        self._default_key = DEFAULT_PERSONA_KEY
        self.reload()

    def reload(self) -> None:
        with self._lock:
            with self.builtins_path.open("r", encoding="utf-8") as source:
                builtins_data = json.load(source)

            self._shared_prompt = str(builtins_data.get("shared_prompt", "")).strip()
            self._builtins = {
                persona.key: persona
                for persona in (
                    Persona.from_dict(item) for item in builtins_data.get("personas", [])
                )
            }
            if DEFAULT_PERSONA_KEY not in self._builtins:
                raise ValueError("Public persona configuration must define ari")

            state = self._read_state()
            self._overrides = {
                persona.key: persona
                for persona in (
                    Persona.from_dict(item)
                    for item in state.get("overrides", {}).values()
                )
            }
            self._deleted = {
                normalize_persona_key(key)
                for key in state.get("deleted", [])
                if key != DEFAULT_PERSONA_KEY
            }
            requested_default = normalize_persona_key(
                str(state.get("default", DEFAULT_PERSONA_KEY))
            )
            self._default_key = (
                requested_default
                if requested_default in self._merged()
                else DEFAULT_PERSONA_KEY
            )

    def _read_state(self) -> dict:
        try:
            with self.state_path.open("r", encoding="utf-8") as source:
                state = json.load(source)
            return state if isinstance(state, dict) else {}
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as error:
            print(f"Could not load persona state; using public defaults: {error}")
            return {}

    def _merged(self) -> dict[str, Persona]:
        personas = dict(self._builtins)
        personas.update(self._overrides)
        for key in self._deleted:
            personas.pop(key, None)
        return personas

    def _write_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "default": self._default_key,
            "overrides": {
                key: asdict(persona)
                for key, persona in sorted(self._overrides.items())
            },
            "deleted": sorted(self._deleted),
        }
        temporary_path = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        with temporary_path.open("w", encoding="utf-8") as target:
            json.dump(state, target, ensure_ascii=False, indent=2, sort_keys=True)
            target.write("\n")
        os.replace(temporary_path, self.state_path)

    @staticmethod
    def _validate(persona: Persona) -> Persona:
        key = normalize_persona_key(persona.key)
        display_name = persona.display_name.strip()
        prompt = persona.prompt.strip()
        avatar_url = persona.avatar_url.strip()
        if not display_name or len(display_name) > 80:
            raise ValueError("Display name must be between 1 and 80 characters")
        if not prompt:
            raise ValueError("Persona prompt cannot be empty")
        if avatar_url and not avatar_url.startswith(("https://", "http://")):
            raise ValueError("Avatar must be an HTTP or HTTPS URL")
        return replace(
            persona,
            key=key,
            display_name=display_name,
            prompt=prompt,
            avatar_url=avatar_url,
        )

    def all(self) -> list[Persona]:
        with self._lock:
            return [self._merged()[key] for key in sorted(self._merged())]

    def get(self, key: str) -> Persona | None:
        try:
            normalized = normalize_persona_key(key)
        except ValueError:
            return None
        with self._lock:
            return self._merged().get(normalized)

    def default(self) -> Persona:
        with self._lock:
            return self._merged().get(
                self._default_key, self._builtins[DEFAULT_PERSONA_KEY]
            )

    @property
    def default_key(self) -> str:
        return self.default().key

    def webhook_personas(self) -> list[Persona]:
        return [persona for persona in self.all() if not persona.use_bot_identity]

    def save(self, persona: Persona) -> Persona:
        persona = self._validate(persona)
        with self._lock:
            self._overrides[persona.key] = persona
            self._deleted.discard(persona.key)
            self._write_state()
        return persona

    def update(self, key: str, field: str, value: str) -> Persona:
        persona = self.get(key)
        if persona is None:
            raise KeyError(f"Unknown persona: {key}")
        field = field.strip().lower().replace("-", "_")
        aliases = {"name": "display_name", "avatar": "avatar_url"}
        field = aliases.get(field, field)
        if field not in {"display_name", "avatar_url", "prompt"}:
            raise ValueError("Editable fields are name, avatar, and prompt")
        return self.save(replace(persona, **{field: value}))

    def delete(self, key: str) -> None:
        key = normalize_persona_key(key)
        if key == DEFAULT_PERSONA_KEY:
            raise ValueError("The built-in ari persona cannot be deleted")
        with self._lock:
            if key not in self._merged():
                raise KeyError(f"Unknown persona: {key}")
            self._overrides.pop(key, None)
            if key in self._builtins:
                self._deleted.add(key)
            if self._default_key == key:
                self._default_key = DEFAULT_PERSONA_KEY
            self._write_state()

    def reset(self, key: str) -> Persona:
        key = normalize_persona_key(key)
        with self._lock:
            if key not in self._builtins:
                raise KeyError(f"No public persona to reset: {key}")
            self._overrides.pop(key, None)
            self._deleted.discard(key)
            self._write_state()
            return self._builtins[key]

    def set_default(self, key: str) -> Persona:
        persona = self.get(key)
        if persona is None:
            raise KeyError(f"Unknown persona: {key}")
        with self._lock:
            self._default_key = persona.key
            self._write_state()
        return persona

    def system_prompt(self, persona: Persona | None = None) -> str:
        persona = persona or self.default()
        now = datetime.datetime.now().astimezone()
        return (
            f"The current local time is {now.strftime('%A, %Y-%m-%d %H:%M:%S %Z')}.\n"
            f"{self._shared_prompt}\n\nPersona:\n{persona.prompt}"
        )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
persona_store = PersonaStore(
    PROJECT_ROOT / "resources" / "personas.json",
    PROJECT_ROOT / "resources" / "personas_state.json",
)
