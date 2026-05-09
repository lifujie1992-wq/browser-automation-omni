from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

RUNTIME = Path(os.environ.get('BROWSER_OMNI_RUNTIME', str(Path.home() / 'browser-omni-runtime')))
CONFIG_DIR = RUNTIME / 'configs'
REGISTRY = RUNTIME / 'contexts' / 'registry.json'


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding='utf-8'))


def load_registry() -> dict[str, Any]:
    return load_json(REGISTRY)


def load_profile(name: str) -> dict[str, Any]:
    return load_registry()['profiles'][name]


def load_platform_config(platform: str) -> dict[str, Any]:
    return load_json(CONFIG_DIR / f'{platform}.json')


def resolve_env_placeholders(value: str) -> str:
    # Preserve public repo placeholders while allowing local runtime execution.
    out = value
    env_defaults = {
        'BROWSER_OMNI_RUNTIME': str(RUNTIME),
        'CLOAKBROWSER_HOME': str(Path.home() / '.cloakbrowser'),
        'CLOAKBROWSER_PROFILE_DIR': str(Path.home() / '.cloakbrowser' / 'profiles'),
        'TOOLS_DIR': str(Path.home() / 'github-tools'),
        'CLOAKBROWSER_REPO': str(Path.home() / 'github-tools' / 'CloakBrowser'),
        'CLOAKBROWSER_PY': str(Path.home() / 'github-tools' / 'CloakBrowser' / '.venv' / 'bin' / 'python'),
    }
    for key, default in env_defaults.items():
        out = out.replace('${' + key + '}', os.environ.get(key, default))
    return out


def resolve_profile(profile: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(profile)
    for key in ['profile_dir', 'source_repo', 'venv_python']:
        if isinstance(resolved.get(key), str):
            resolved[key] = resolve_env_placeholders(resolved[key])
    return resolved
