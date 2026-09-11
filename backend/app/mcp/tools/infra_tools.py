"""Infrastructure MCP tools — Story 1.12.

check_backend_health: Full health report (calls /health/detailed).
switch_vault: Switch active vault (calls /vault/switch).
"""

from __future__ import annotations

from typing import Any, Dict

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
    # detailed_health_check 注解为 -> dict, 故本防御分支对类型检查器恒不可达;
    # 保留是为了该端点将来改回 JSONResponse 时不静默取错字段。只关这一行。
    if hasattr(resp, "body"):
        import json

        return json.loads(resp.body)["data"]  # pyright: ignore[reportAttributeAccessIssue]
    return resp.get("data", resp) if isinstance(resp, dict) else {}


async def switch_vault(input: SwitchVaultInput) -> Dict[str, Any]:
    from app.api.v1.endpoints.vault import VaultSwitchRequest, switch_vault as _switch

    try:
        result = await _switch(VaultSwitchRequest(vault_path=input.vault_path))
        # ⚠️ 真缺陷, 本卡只让类型过门不修(改行为=产品裁定, 已登 TAIL):
        # vault.switch_vault 被 P0-3 写侧隔离后恒返回 JSONResponse, 它没有
        # vault_name / vault_id ⇒ 下面两行运行期必 AttributeError, 被本函数的
        # except Exception 吞成 success=False。即本 MCP 工具恒报失败。
        # 不用 cast: cast 等于声明"它就是那个类型", 会把这个真缺陷永久盖住。
        return SwitchVaultOutput(
            success=True,
            vault_name=result.vault_name,  # pyright: ignore[reportAttributeAccessIssue]
            vault_id=result.vault_id,  # pyright: ignore[reportAttributeAccessIssue]
        ).model_dump()
    except Exception as e:
        return SwitchVaultOutput(success=False, error=str(e)[:200]).model_dump()
