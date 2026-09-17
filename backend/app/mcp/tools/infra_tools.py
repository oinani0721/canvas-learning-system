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
    import json

    from app.api.v1.endpoints.vault import VaultSwitchRequest, switch_vault as _switch

    try:
        result = await _switch(VaultSwitchRequest(vault_path=input.vault_path))
        # vault.switch_vault 被 P0-3 写侧隔离后恒返回 410 JSONResponse, body =
        # {"error": "gone", "detail": ...} —— 它没有 vault_name / vault_id。原先直接
        # 读 result.vault_name 必 AttributeError, 被下面的 except 吞成
        # "'JSONResponse' object has no attribute 'vault_name'": 一句与真实原因无关
        # 的内部类型错误。改为解析 body, 把真实原因(隔离说明)透传给调用方。
        # ⛔ 不用 cast: cast 等于声明"它就是那个类型", 会把这类真缺陷永久盖住。
        # bytes(): body 静态类型是 bytes | memoryview[int], json.loads 不收 memoryview。
        try:
            payload = json.loads(bytes(result.body))
        except (TypeError, ValueError) as exc:
            reason = f"vault switch response body is not valid JSON (HTTP {result.status_code}): {exc}"
            return SwitchVaultOutput(success=False, error=reason[:200]).model_dump()

        # ⛔ body 不是 JSON 对象时必须判失败, 不能落进下面的 success 分支:
        # 那等于把"读不出字段"谎报成切换成功 —— 比原缺陷更坏(原缺陷至少 success=False)。
        if not isinstance(payload, dict):
            reason = f"vault switch response body is not a JSON object (HTTP {result.status_code}): {payload!r}"
            return SwitchVaultOutput(success=False, error=reason[:200]).model_dump()

        if result.status_code >= 400 or "error" in payload:
            detail = payload.get("detail") or payload.get("error")
            # detail 缺失时不落成字符串 "None" —— 那又是一句无信息量的文案。
            reason = str(detail) if detail else f"vault switch failed with HTTP {result.status_code}"
            return SwitchVaultOutput(success=False, error=reason[:200]).model_dump()

        return SwitchVaultOutput(
            success=True,
            vault_name=str(payload.get("vault_name") or ""),
            vault_id=str(payload.get("vault_id") or ""),
        ).model_dump()
    except Exception as e:
        # 带上异常类型名: 空消息异常(如 RuntimeError())的 str(e) 是空串, 调用方拿到
        # error="" —— 又是一句没有信息量的文案, 正是本卡要消除的那种形态。
        reason = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
        return SwitchVaultOutput(success=False, error=reason[:200]).model_dump()
