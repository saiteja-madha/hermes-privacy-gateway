#!/usr/bin/env python3
"""Run after dependencies and en_core_web_lg are installed."""

import os
from pathlib import Path

from privacy import PrivacyEngine

if not os.environ.get("HERMES_PRIVACY_GATEWAY_KEY"):
    raise SystemExit("Set HERMES_PRIVACY_GATEWAY_KEY first")

engine = PrivacyEngine(Path(__file__).resolve().parents[1] / "nlp.yaml")
source = "John Smith can be reached at john.smith@example.com."
san = engine.sanitize(source)
print("source:   ", source)
print("sanitized:", san)
print("restored: ", engine.rehydrate(san))
