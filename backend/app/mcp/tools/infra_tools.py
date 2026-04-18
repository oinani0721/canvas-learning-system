"""Infrastructure MCP tools — Story 1.12.

check_backend_health: Full health report (calls /health/detailed).
switch_vault: Switch active vault (calls /vault/switch).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CheckHealthInput(BaseModel):
    pass


class CheckHealthOutput(BaseModel):
    overall_status: str
    components: list[Dict[str, Any]]


class SwitchVaultInput(BaseModel):
    vault_path: str = Field(
        ...,
        description="Absolute path to the target Obsidian vault (must contain .obsidian/)",
    )


class SwitchVaultOutput(BaseModel):
    success: bool
    vault_name: str = ""
    vault_id: str = ""
    error: str = ""


async def check_backend_health(input: CheckHealthInput) -> Dict[str, Any]:
    from app.config import get_settings
    from app.api.v1.system import detailed_health_check

    resp = await detailed_health_check(settings=get_settings())
    if hasattr(resp, "body"):
        import json

        return json.loads(resp.body)["data"]
    return resp.get("data", resp) if isinstance(resp, dict) else {}


async def switch_vault(input: SwitchVaultInput) -> Dict[str, Any]:
    from app.api.v1.endpoints.vault import VaultSwitchRequest, switch_vault as _switch

    try:
        result = await _switch(VaultSwitchRequest(vault_path=input.vault_path))
        return SwitchVaultOutput(
            success=True,
            vault_name=result.vault_name,
            vault_id=result.vault_id,
        ).model_dump()
    except Exception as e:
        return SwitchVaultOutput(success=False, error=str(e)[:200]).model_dump()
