#!/usr/bin/env python3
"""Throttle agent instructions to check for updates before offering a manual update."""

import fcntl
import os
from pathlib import Path
import time


def main():
    try:
        days = int(os.environ.get("BENTO_UPDATE_REMINDER_DAYS", "30"))
        if days <= 0:
            return
        state = Path(os.environ.get(
            "BENTO_UPDATE_REMINDER_STATE",
            str(Path.home() / ".bento" / "update-reminder"),
        ))
        state.parent.mkdir(parents=True, exist_ok=True)
        # One timestamp across agents, repos, and worktrees. Concurrent starts
        # skip immediately; the OS releases the lock even if the hook is killed.
        with state.open("a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            handle.seek(0)
            try:
                last = int(handle.read().strip())
            except ValueError:
                last = 0
            now = int(time.time())
            if 0 < last <= now and now - last < days * 86400:
                return
            handle.seek(0)
            handle.truncate()
            handle.write(str(now))
            handle.flush()
        print(
            "A periodic Bento update check is due. Before mentioning updates to the "
            "user, check for a newer version automatically using read-only checks: "
            "compare the installed Bento revision/version with its configured "
            "upstream for the active install mode. The submodule pin and Claude's "
            "installed plugin cache are separate; inspect the one actually in use. "
            "Only if you confirm a newer version is available, briefly report the "
            "installed and available revisions/versions and ask whether the user "
            "wants to update. If already current, offline, or unable to establish "
            "that the upstream is newer, stay silent about updates and continue "
            "the user's task. Bento updates remain manual: follow Bento README's "
            "Update instructions only when the user chooses to update. Do not "
            "update the submodule or plugins automatically."
        )
    except (OSError, ValueError):
        # Unavailable state or invalid configuration must never block a session.
        return


if __name__ == "__main__":
    main()
