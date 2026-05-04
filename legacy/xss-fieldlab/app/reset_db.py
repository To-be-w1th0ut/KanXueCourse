from __future__ import annotations

import sys

from storage import init_db, reset_target


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    init_db(force=False)
    reset_target(target)
    print(f"reset completed: {target}")
