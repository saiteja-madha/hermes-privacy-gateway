"""register() must not depend on Presidio being importable.

If it did, a missing dependency would make plugin registration fail, no
middleware would be installed, and Hermes would send plaintext to the provider.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = "privacy_gateway_under_test"


class FakeCtx:
    def __init__(self):
        self.middleware = {}
        self.hooks = {}

    def get_config(self, key, default=None):
        return default

    def register_middleware(self, name, fn):
        self.middleware[name] = fn

    def register_hook(self, name, fn):
        self.hooks[name] = fn


def test_register_without_presidio_blocks_requests(monkeypatch):
    for name in list(sys.modules):
        if name == "presidio_analyzer" or name.startswith("presidio_analyzer."):
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, "presidio_analyzer", None)  # import -> ImportError

    spec = importlib.util.spec_from_file_location(
        PKG, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = module
    try:
        spec.loader.exec_module(module)
        ctx = FakeCtx()
        module.register(ctx)

        assert set(ctx.middleware) == {"llm_request", "tool_request"}
        out = ctx.middleware["llm_request"](
            request={
                "model": "m",
                "messages": [{"role": "user", "content": "Alice Example, alice@example.com"}],
            }
        )
        assert out["request"]["messages"] == [
            {"role": "user", "content": "[PRIVACY_GATEWAY_BLOCKED_REQUEST]"}
        ]
    finally:
        for name in list(sys.modules):
            if name == PKG or name.startswith(PKG + "."):
                del sys.modules[name]
