"""Shared limits for the contour-focused body rebuild and installation."""
import fnmatch
import json
from pathlib import Path


def load_policy():
    return json.loads(Path(__file__).with_name('policy.json').read_text(encoding='utf-8'))


def excluded_name(name, policy=None):
    policy = load_policy() if policy is None else policy
    return any(fnmatch.fnmatchcase(name.lower(), pattern.lower())
               for pattern in policy['excluded_name_patterns'])
