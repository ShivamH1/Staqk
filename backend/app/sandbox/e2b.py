"""Async wrapper around the E2B sandbox.

User-generated code runs *only* inside the sandbox, never on the host. The
sandbox is an external resource and must always be released — use
`sandbox_session()`, which kills the sandbox in a `finally` block even when the
body raises.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from e2b import AsyncSandbox, CommandExitException
from e2b.sandbox.filesystem.filesystem import WriteEntry

from app.config import settings

logger = logging.getLogger(__name__)

# Hard ceiling on a sandbox's lifetime; the whole build must finish within it.
SANDBOX_TIMEOUT = 300
# Per-command ceiling (npm install / build can be slow on a cold sandbox).
COMMAND_TIMEOUT = 240
# All project files live here; build commands run with this as the cwd.
WORK_DIR = "/home/user/app"


@dataclass(frozen=True)
class CommandOutcome:
    exit_code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    def log_tail(self, limit: int = 4000) -> str:
        """Combined stderr+stdout, truncated for use as LLM retry context."""
        combined = f"{self.stderr}\n{self.stdout}".strip()
        if len(combined) <= limit:
            return combined
        return combined[-limit:]


class Sandbox:
    """Owns a single E2B sandbox. Construct via `sandbox_session()`."""

    def __init__(self, inner: AsyncSandbox) -> None:
        self._inner = inner

    async def write_files(self, files: dict[str, str]) -> None:
        """Write a {path: content} map under the project work dir."""
        if not files:
            return
        entries = [
            WriteEntry(path=f"{WORK_DIR}/{path}", data=content) for path, content in files.items()
        ]
        await self._inner.files.write_files(entries)

    async def read_file(self, path: str) -> str:
        result = await self._inner.files.read(f"{WORK_DIR}/{path}")
        return result if isinstance(result, str) else result.decode()

    async def run(self, cmd: str, timeout: float = COMMAND_TIMEOUT) -> CommandOutcome:  # noqa: ASYNC109 — forwards to E2B's own command timeout
        """Run a shell command in the work dir; non-zero exit is returned, not raised."""
        try:
            res = await self._inner.commands.run(cmd, cwd=WORK_DIR, timeout=timeout)
            return CommandOutcome(res.exit_code, res.stdout, res.stderr)
        except CommandExitException as exc:
            return CommandOutcome(exc.exit_code, exc.stdout, exc.stderr)


@asynccontextmanager
async def sandbox_session() -> AsyncIterator[Sandbox]:
    """Yield a sandbox, guaranteeing it is killed on exit."""
    if not settings.e2b_api_key:
        raise RuntimeError("E2B_API_KEY is not configured")
    inner = await AsyncSandbox.create(
        template=settings.e2b_template or None,
        timeout=SANDBOX_TIMEOUT,
        api_key=settings.e2b_api_key,
    )
    logger.info("E2B sandbox created: %s", inner.sandbox_id)
    try:
        yield Sandbox(inner)
    finally:
        await inner.kill()
        logger.info("E2B sandbox killed: %s", inner.sandbox_id)
