import json
import os
from pathlib import Path

from browser_omni_runtime.common.io import atomic_write_json, locked_append_jsonl, read_json


def test_atomic_write_json(tmp_path: Path):
    target = tmp_path / 'data.json'
    atomic_write_json(target, {'ok': True, 'n': 1})
    assert read_json(target) == {'ok': True, 'n': 1}
    assert not list(tmp_path.glob('*.tmp'))


def test_locked_append_jsonl(tmp_path: Path):
    target = tmp_path / 'audit.jsonl'
    locked_append_jsonl(target, {'a': 1})
    locked_append_jsonl(target, {'b': 2})
    lines = target.read_text(encoding='utf-8').splitlines()
    assert [json.loads(line) for line in lines] == [{'a': 1}, {'b': 2}]
