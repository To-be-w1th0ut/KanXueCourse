from __future__ import annotations

import sys

from content_store import init_content_db, reset_content

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'all'
    init_content_db(force=False)
    reset_content(target)
    print(f'content reset completed: {target}')
