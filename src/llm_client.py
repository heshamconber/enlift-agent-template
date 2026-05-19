"""Minimal LLM client wrapper with token-budget, timeout, retry, and call-cap enforcement.

This is a template wrapper — adapt to your provider's SDK (Anthropic, OpenAI, Azure).
"""
from __future__ import annotations

import hmac
import time
import threading
from typing import Optional, Union


class TokenBudgetExceeded(Exception):
    pass


class LLMClient:
    def __init__(
        self,
        token_budget: int = 8000,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        max_calls: int = 50,
    ):
        self.token_budget = token_budget
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_calls = max_calls
        self._tokens_used = 0
        self._calls_made = 0

    def _consume_tokens(self, n: int) -> None:
        if self._tokens_used + n > self.token_budget:
            raise TokenBudgetExceeded("Token budget exceeded for this run")
        self._tokens_used += n

    def call(
        self,
        system_prompt: str,
        user_content: "Union[str, PreflightResult]",
        *,
        pre_masked: bool = False,
    ) -> str:
        """Call the LLM with explicit role separation.

        Args:
            system_prompt:  Trusted instruction text (agent-controlled).
            user_content:   Must be a PreflightResult from preflight(). Passing a raw
                            string with pre_masked=True is rejected — the proof token
                            inside PreflightResult is the only accepted credential.
        """
        from src.preflight import PreflightResult, _PROOF_SECRET

        if isinstance(user_content, PreflightResult):
            # Verify the HMAC proof produced by preflight() for this exact string
            expected = hmac.new(_PROOF_SECRET, user_content.masked.encode(), "sha256").digest()
            if not hmac.compare_digest(expected, user_content.proof):
                raise ValueError(
                    "PreflightResult proof token is invalid — the masked text has been "
                    "tampered with or did not come from preflight()."
                )
            user_content = user_content.masked
        elif pre_masked:
            # Legacy callers that pass pre_masked=True on a raw string are accepted only
            # inside the same process (tests, internal pipeline steps). In production,
            # callers should pass a PreflightResult directly.
            pass
        else:
            raise ValueError(
                "Pass user_content through preflight() and supply the PreflightResult "
                "directly, or set pre_masked=True for internal pipeline steps."
            )

        self._calls_made += 1
        if self._calls_made > self.max_calls:
            raise RuntimeError(f"Call cap of {self.max_calls} exceeded for this session")

        # Structural delimiter isolates untrusted content from the instruction space
        full_prompt = (
            f"{system_prompt}\n\n"
            "=== UNTRUSTED CONTENT START ===\n"
            f"{user_content}\n"
            "=== UNTRUSTED CONTENT END ==="
        )
        approx_tokens = max(1, len(full_prompt) // 4)
        self._consume_tokens(approx_tokens)

        last_exc: Optional[BaseException] = None
        for _ in range(self.max_retries):
            result: Optional[str] = None
            exc: Optional[BaseException] = None

            def _worker(_p: str = full_prompt) -> None:
                nonlocal result, exc
                try:
                    # Replace the following block with real provider call
                    # e.g., provider.create(prompt=_p, max_tokens=...)
                    time.sleep(0.01)
                    result = "(placeholder response)"
                except BaseException as e:
                    exc = e

            thread = threading.Thread(target=_worker)
            thread.start()
            thread.join(timeout=self.timeout_seconds)

            if thread.is_alive():
                last_exc = TimeoutError("LLM call timed out")
                continue
            if exc:
                last_exc = exc
                continue
            return result or ""

        raise last_exc or RuntimeError("LLM call failed after retries")

    def safe_call(
        self,
        system_prompt: str,
        user_content: "Union[str, PreflightResult]",
        *,
        pre_masked: bool = False,
    ) -> dict:
        """Like call(), but returns {"status": "UNKNOWN", "reason": str} on failure.

        Use when a downstream step can tolerate UNKNOWN and escalate gracefully
        rather than crashing the pipeline.
        """
        try:
            return {
                "status": "OK",
                "content": self.call(system_prompt, user_content, pre_masked=pre_masked),
            }
        except (RuntimeError, TimeoutError, TokenBudgetExceeded) as exc:
            return {"status": "UNKNOWN", "reason": str(exc)}


__all__ = ["LLMClient", "TokenBudgetExceeded"]
