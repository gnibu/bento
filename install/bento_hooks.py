"""Shared hook commands and JSON merging that preserves unrelated settings."""
import copy
import json


def hook_command(event, auto_pr=False):
    script = "session-start.sh" if event == "SessionStart" else "session-stop.sh"
    prefix = "BENTO_IMPROVE_AUTO_PR=1 " if auto_pr and event == "Stop" else ""
    return (
        'bento_repo="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0; '
        f'bento_hook="$bento_repo/.bento/plugins/bento-forge/scripts/{script}"; '
        f'[ ! -f "$bento_hook" ] || {prefix}bash "$bento_hook"'
    )


def is_bento_handler(handler, event, command_factory=hook_command):
    """Recognize current and legacy Bento handlers without owning other hooks."""
    if handler.get("type") != "command":
        return False
    command = handler.get("command", "")
    if command in {command_factory(event, False), command_factory(event, True)}:
        return True
    script = "session-start.sh" if event == "SessionStart" else "session-stop.sh"
    return f".bento/plugins/bento-forge/scripts/{script}" in command


def merge_json_hooks(text, purge, auto_pr, command_factory=hook_command):
    data = json.loads(text) if text else {}
    original = copy.deepcopy(data)
    if not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict):
        raise ValueError("hooks.json must contain an object with a hooks object")
    hooks = data.setdefault("hooks", {})
    for event in ("SessionStart", "Stop"):
        groups = hooks.get(event, [])
        if not isinstance(groups, list):
            raise ValueError(f"hooks.{event} must be an array")
        kept = []
        desired = {"type": "command", "command": command_factory(event, auto_pr), "timeout": 5}
        found = False
        for group in groups:
            handlers = group.get("hooks", [])
            remaining = []
            removed = False
            for handler in handlers:
                if is_bento_handler(handler, event, command_factory):
                    if not purge and not found and not group.get("matcher"):
                        remaining.append(desired)
                        found = True
                    removed = True
                else:
                    remaining.append(handler)
            if remaining or not removed:
                kept.append({**group, "hooks": remaining} if removed else group)
        if not purge and not found:
            kept.append({"hooks": [desired]})
        if kept:
            hooks[event] = kept
        elif event in hooks:
            del hooks[event]
    if not hooks and "hooks" not in original:
        del data["hooks"]
    return text if data == original else json.dumps(data, indent=2) + "\n"
