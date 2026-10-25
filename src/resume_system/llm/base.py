from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    text: str
    # OpenAI 兼容格式：[{"id", "type": "function", "function": {"name", "arguments"}}]
    tool_calls: list[dict] = field(default_factory=list)


class LLMClient(ABC):
    """统一的模型接口。

    messages / tools 均使用 OpenAI 兼容格式作为内部规范格式；
    其它厂商（Anthropic、Ollama 等）的适配器负责把自家协议翻译成这个格式。
    agents / tools 只依赖本接口，不依赖任何具体厂商 SDK。
    """

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        ...
