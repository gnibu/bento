"""Shared hook commands and JSON merging that preserves unrelated settings."""
import copy
import json


SCRIPTS = ".bento/plugins/bento-forge/scripts/"
# Bento wires SessionStart only. Stop is still scanned so reruns remove the
# retired learning hook (session-stop.sh) from older installs.
EVENTS = ("SessionStart", "Stop")


def hook_command():
    return (
        'bento_repo="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0; '
        f'bento_hook="$bento_repo/{SCRIPTS}session-start.sh"; '
        '[ ! -f "$bento_hook" ] || bash "$bento_hook"'
    )


def is_bento_handler(handler):
    """Recognize current and legacy Bento handlers without owning other hooks."""
    command = handler.get("command", "")
    return handler.get("type") == "command" and any(
        f"{SCRIPTS}{script}" in command for script in ("session-start.sh", "session-stop.sh"))


def merge_json_hooks(text, purge, command_factory=hook_command):
    data = json.loads(text) if text else {}
    original = copy.deepcopy(data)
    if not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict):
        raise ValueError("hooks.json must contain an object with a hooks object")
    hooks = data.setdefault("hooks", {})
    for event in EVENTS:
        groups = hooks.get(event, [])
        if not isinstance(groups, list):
            raise ValueError(f"hooks.{event} must be an array")
        kept = []
        desired = {"type": "command", "command": command_factory(), "timeout": 5}
        wanted = event == "SessionStart" and not purge
        found = False
        for group in groups:
            handlers = group.get("hooks", [])
            remaining = []
            removed = False
            for handler in handlers:
                if is_bento_handler(handler):
                    if wanted and not found and not group.get("matcher"):
                        remaining.append(desired)
                        found = True
                    removed = True
                else:
                    remaining.append(handler)
            if remaining or not removed:
                kept.append({**group, "hooks": remaining} if removed else group)
        if wanted and not found:
            kept.append({"hooks": [desired]})
        if kept:
            hooks[event] = kept
        elif event in hooks:
            del hooks[event]
    if not hooks and "hooks" not in original:
        del data["hooks"]
    return text if data == original else json.dumps(data, indent=2) + "\n"
