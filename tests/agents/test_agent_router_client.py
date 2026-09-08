import json
from unittest.mock import MagicMock
import pytest
from pydantic import BaseModel

from src.agents.llm_client import AgentRouterLLMClient


class MockSchema(BaseModel):
    result: str


def test_agent_router_client_telemetry_and_parsing():
    """Testa se o cliente parseia JSON corretamente e extrai a telemetria."""
    def mock_transport(method, url, headers, body):
        mock_response = {
            "choices": [{"message": {"content": '{"result": "success"}'}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        return json.dumps(mock_response).encode("utf-8")

    client = AgentRouterLLMClient(api_key="test-key", transport=mock_transport)
    import asyncio
    
    response = asyncio.run(client.generate("sys", "user", MockSchema))
    
    assert isinstance(response, MockSchema)
    assert response.result == "success"
    
    telemetry = client.all_telemetry
    assert len(telemetry) == 1
    assert telemetry[0].prompt_tokens == 10
    assert telemetry[0].completion_tokens == 5
    assert telemetry[0].total_tokens == 15
    assert telemetry[0].latency_ms >= 0


def test_agent_router_client_missing_api_key():
    """Testa se levanta erro de conexão sem API key configurada."""
    client = AgentRouterLLMClient(api_key="")
    import asyncio
    with pytest.raises(ConnectionError, match="LLM_API_KEY não configurada"):
        asyncio.run(client.generate("sys", "user", MockSchema))
