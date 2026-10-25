from __future__ import annotations

import os

from ..config import load_models_config
from .base import LLMClient
from .deepseek import DeepSeekClient


def get_llm(config: dict | None = None) -> LLMClient:
    """根据配置返回对应厂商的客户端。换模型 = 改 config/models.yaml 里的 provider/model。"""
    cfg = config or load_models_config()
    provider = str(cfg.get("provider", "")).lower()

    if provider == "deepseek":
        return DeepSeekClient(
            model=cfg["model"],
            base_url=cfg["base_url"],
            api_key=os.environ.get(cfg["api_key_env"], ""),
            temperature=cfg.get("temperature", 0.3),
            max_tokens=cfg.get("max_tokens", 4096),
        )

    # 在这里注册新的 provider（openai / anthropic / ollama ...）
    raise ValueError(f"未注册的 provider: {provider}，请在 factory.py 里添加对应适配器")
