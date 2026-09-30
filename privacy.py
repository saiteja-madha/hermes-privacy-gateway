"""Presidio-backed text pseudonymization and local alias rehydration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

try:
    from .vault import AliasVault, alias_ranges
except ImportError:  # direct local test/import outside Hermes plugin loader
    from vault import AliasVault, alias_ranges


BLOCKED_REQUEST = "[PRIVACY_GATEWAY_BLOCKED_REQUEST]"
BLOCKED_TOOL_RESULT = "[PRIVACY_GATEWAY_BLOCKED_TOOL_RESULT]"
NON_TEXT_BLOCK = "[PRIVACY_GATEWAY_BLOCKED_NON_TEXT_CONTENT]"

# Conservative structured-secret patterns. These are deliberately narrow;
# domain-specific secrets should be added as Presidio recognizers or local rules.
_PEM_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)
_AUTH_HEADER = re.compile(
    r"(?im)^authorization\s*:\s*(?:bearer|basic)\s+\S+\s*$"
)

_NON_TEXT_TYPES = {
    "image_url",
    "input_image",
    "image",
    "input_audio",
    "audio",
    "input_file",
    "file",
}
_NON_TEXT_KEYS = {
    "image_url",
    "file_data",
    "b64_json",
    "input_audio",
    "audio_url",
}


def walk_strings(value: Any, string_fn) -> Any:
    """Recursively transform strings while preserving container structure."""
    if isinstance(value, str):
        return string_fn(value)
    if isinstance(value, list):
        return [walk_strings(item, string_fn) for item in value]
    if isinstance(value, tuple):
        return tuple(walk_strings(item, string_fn) for item in value)
    if isinstance(value, dict):
        return {key: walk_strings(item, string_fn) for key, item in value.items()}
    return value


def contains_non_text_model_content(value: Any) -> bool:
    """Detect common provider payload shapes carrying image/audio/file content."""
    if isinstance(value, list) or isinstance(value, tuple):
        return any(contains_non_text_model_content(item) for item in value)
    if isinstance(value, dict):
        item_type = str(value.get("type", "")).lower()
        if item_type in _NON_TEXT_TYPES:
            return True
        if any(key in value for key in _NON_TEXT_KEYS):
            return True
        return any(contains_non_text_model_content(item) for item in value.values())
    return False


def blocked_content_for_key(key: str) -> Any:
    """Return a conservative provider-compatible replacement for common text roots."""
    if key == "messages":
        return [{"role": "user", "content": BLOCKED_REQUEST}]
    return BLOCKED_REQUEST


class PrivacyEngine:
    """Local detector + stable pseudonymizer."""

    def __init__(
        self,
        nlp_config_path: Path,
        *,
        language: str = "en",
        score_threshold: float = 0.55,
        enable_langextract: bool = False,
        langextract_config_path: str = "",
        vault: AliasVault | None = None,
    ) -> None:
        self.language = language
        self.score_threshold = score_threshold
        self.vault = vault or AliasVault()

        provider = NlpEngineProvider(conf_file=str(nlp_config_path))
        nlp_engine = provider.create_engine()
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=[language],
        )
        self.anonymizer = AnonymizerEngine()

        if enable_langextract:
            from presidio_analyzer.predefined_recognizers.third_party.basic_langextract_recognizer import (
                BasicLangExtractRecognizer,
            )

            if langextract_config_path:
                recognizer = BasicLangExtractRecognizer(
                    config_path=langextract_config_path
                )
            else:
                recognizer = BasicLangExtractRecognizer()
            self.analyzer.registry.add_recognizer(recognizer)

    @staticmethod
    def remove_high_confidence_secrets(text: str) -> str:
        text = _PEM_PRIVATE_KEY.sub("[SECRET_REMOVED]", text)
        return _AUTH_HEADER.sub("Authorization: [SECRET_REMOVED]", text)

    def sanitize(self, text: str) -> str:
        """Replace detected PII with stable aliases; never alias secrets."""
        if not text:
            return text

        text = self.remove_high_confidence_secrets(text)
        protected = alias_ranges(text)
        results = self.analyzer.analyze(
            text=text,
            language=self.language,
            score_threshold=self.score_threshold,
        )

        # Do not feed already-issued aliases back through Presidio.
        if protected:
            results = [
                result
                for result in results
                if not any(
                    result.start < end and result.end > start
                    for start, end in protected
                )
            ]

        if not results:
            return text

        entity_types = {result.entity_type for result in results}
        operators = {
            entity_type: OperatorConfig(
                "custom",
                {
                    "lambda": (
                        lambda value, entity_type=entity_type: self.vault.alias(
                            entity_type, value
                        )
                    )
                },
            )
            for entity_type in entity_types
        }

        return self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        ).text

    def sanitize_tree(self, value: Any) -> Any:
        return walk_strings(value, self.sanitize)

    def rehydrate(self, text: str) -> str:
        return self.vault.rehydrate(text)

    def rehydrate_tree(self, value: Any) -> Any:
        return walk_strings(value, self.rehydrate)
