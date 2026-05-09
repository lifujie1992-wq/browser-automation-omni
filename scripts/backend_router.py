#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from browser_omni_runtime.common.backend_router import choose_backend


def main() -> int:
    parser = argparse.ArgumentParser(description='Choose browser automation backend for a task')
    parser.add_argument('task', help='Task description')
    parser.add_argument('--platform', default=None, help='Optional platform name, e.g. shop_admin/taobao/1688')
    parser.add_argument('--context-json', default='{}', help='Optional JSON context')
    args = parser.parse_args()

    context = json.loads(args.context_json)
    decision = choose_backend(args.task, platform=args.platform, context=context)
    print(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
