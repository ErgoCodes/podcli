"""Load a .env file without letting it hijack the process environment.

A .env can end up containing attacker-influenced lines (planted project files,
imported bundles). Variables that change how interpreters or the dynamic linker
load code are never accepted from it.
"""
from __future__ import annotations

import os

_DENIED_EXACT = {
    "PATH", "HOME", "SHELL", "IFS", "BASH_ENV", "ENV", "PROMPT_COMMAND",
    "NODE_OPTIONS", "NODE_PATH", "NODE_EXTRA_CA_CERTS",
    "PERL5OPT", "PERL5LIB", "RUBYOPT", "RUBYLIB",
    "GIT_SSH_COMMAND", "GIT_EXEC_PATH", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
}
_DENIED_PREFIXES = ("PYTHON", "LD_", "DYLD_")


def is_denied_key(key: str) -> bool:
    k = key.strip().upper()
    return k in _DENIED_EXACT or k.startswith(_DENIED_PREFIXES)


def parse_env_file(path: str) -> dict[str, str]:
    if not path or not os.path.isfile(path):
        return {}
    try:
        from dotenv import dotenv_values
        raw = dotenv_values(path)
    except ImportError:
        raw = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    raw[k.strip()] = v.strip()
    return {k: v for k, v in raw.items() if k and v and not is_denied_key(k)}


def load_env_file(path: str) -> None:
    for k, v in parse_env_file(path).items():
        os.environ.setdefault(k, v)
