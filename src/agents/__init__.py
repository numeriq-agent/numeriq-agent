from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol

try:  # pragma: no cover - exercised only when dependency available
    from google.agent import Agent as GoogleAgent  # type: ignore
except ImportError:  # pragma: no cover - fallback for local/dev usage
    GoogleAgent = None  # type: ignore


class Tool(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...


@dataclass
class AgentMemory:
    """Minimal state container used when the Google Agent SDK is not installed."""

    state: Dict[str, Any] = field(default_factory=dict)

    def update(self, **kwargs: Any) -> None:
        self.state.update(kwargs)

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)


class BaseAgent:
    """Wrapper that integrates with the Google Agent Development Kit when available."""

    def __init__(self, name: str, tool: Tool, memory: AgentMemory | None = None):
        self.name = name
        self.tool = tool
        self.memory = memory or AgentMemory()
        if GoogleAgent is not None:
            self._delegate = GoogleAgent(name=name, tool=tool)  # pragma: no cover
        else:
            self._delegate = None

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if self._delegate is not None:  # pragma: no cover
            result = self._delegate.run(*args, **kwargs)
        else:
            result = self.tool(*args, **kwargs)
        self.memory.update(last_result=result)
        return result

