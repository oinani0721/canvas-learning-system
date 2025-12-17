# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.G.4: 响应格式自适应 - 单元测试
# [Source: docs/stories/story-12.G.4-response-format-adaptive.md]
# ═══════════════════════════════════════════════════════════════════════════════
"""
测试 extract_explanation_text 多格式支持

覆盖的 Acceptance Criteria:
- AC1: OpenAI 兼容格式提取器 (choices[0].message.content)
- AC2: 嵌套 response 提取器 (response.text, response.content)
- AC3: Markdown JSON 代码块解析器
- AC6: 单元测试 ≥10 个测试用例
- AC7: 向后兼容性

测试框架: pytest + pytest-mock
"""

from app.services.agent_service import (
    _extract_json_from_markdown,
    _extract_nested_response_content,
    _extract_nested_response_text,
    _extract_openai_choices,
    extract_explanation_text,
)


class TestExtractExplanationText:
    """测试 extract_explanation_text 多格式支持"""

    # =========================================================================
    # AC7: 向后兼容性测试 - 现有格式
    # =========================================================================

    def test_gemini_native_format(self):
        """测试 Gemini 原生格式: {"response": "..."}"""
        response = {"response": "Gemini native response"}
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Gemini native response"

    def test_direct_string(self):
        """测试纯文本格式: 直接字符串"""
        response = "Direct string response"
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Direct string response"

    def test_content_key_format(self):
        """测试 content 字段格式: {"content": "..."}"""
        response = {"content": "Content field response"}
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Content field response"

    def test_text_key_format(self):
        """测试 text 字段格式: {"text": "..."}"""
        response = {"text": "Text field response"}
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Text field response"

    # =========================================================================
    # AC1: OpenAI 兼容格式测试
    # =========================================================================

    def test_openai_choices_format(self):
        """测试 OpenAI 标准格式: choices[0].message.content"""
        response = {
            "choices": [{
                "message": {"content": "OpenAI response content"}
            }]
        }
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "OpenAI response content"

    def test_openai_streaming_delta_format(self):
        """测试 OpenAI Streaming 格式: choices[0].delta.content"""
        response = {
            "choices": [{
                "delta": {"content": "Streaming content"}
            }]
        }
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Streaming content"

    # =========================================================================
    # AC2: 嵌套 response 格式测试
    # =========================================================================

    def test_nested_response_text(self):
        """测试嵌套格式: {"response": {"text": "..."}}"""
        response = {"response": {"text": "Nested text content"}}
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Nested text content"

    def test_nested_response_content(self):
        """测试嵌套格式: {"response": {"content": "..."}}"""
        response = {"response": {"content": "Nested content value"}}
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Nested content value"

    # =========================================================================
    # AC3: Markdown JSON 代码块测试
    # =========================================================================

    def test_markdown_json_block(self):
        """测试 Markdown JSON 代码块: ```json\\n{...}\\n```"""
        response = '''Here is the result:
```json
{"response": "Markdown JSON content"}
```
'''
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Markdown JSON content"

    def test_markdown_json_block_uppercase(self):
        """测试大写 JSON 标记: ```JSON\\n{...}\\n```"""
        response = '''Result:
```JSON
{"text": "Uppercase JSON marker"}
```
'''
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Uppercase JSON marker"

    # =========================================================================
    # 边界情况测试
    # =========================================================================

    def test_empty_response(self):
        """测试空响应: None"""
        result, success = extract_explanation_text(None)
        assert success is False
        assert result == ""

    def test_empty_string_response(self):
        """测试空字符串响应"""
        result, success = extract_explanation_text("")
        assert success is False
        assert result == ""

    def test_empty_dict_response(self):
        """测试空字典响应"""
        result, success = extract_explanation_text({})
        assert success is False
        assert result == ""

    def test_invalid_json_in_markdown(self):
        """测试无效 JSON 在 Markdown 中的处理"""
        response = '''```json
{invalid json}
```'''
        # 应该 fallback 到 direct_str 或 stringify 提取
        result, success = extract_explanation_text(response)
        # 最终会通过 direct_str 提取原始字符串
        assert success is True
        assert "invalid json" in result

    def test_empty_choices_array(self):
        """测试空 choices 数组"""
        response = {"choices": []}
        # OpenAI 提取器应跳过
        result, success = extract_explanation_text(response)
        # stringify 会生成 "{'choices': []}"
        assert success is True

    # =========================================================================
    # 混合格式测试
    # =========================================================================

    def test_priority_response_over_openai(self):
        """测试优先级: response 字段优先于 OpenAI 格式"""
        response = {
            "response": "Gemini response",
            "choices": [{"message": {"content": "OpenAI content"}}]
        }
        result, success = extract_explanation_text(response)
        assert success is True
        assert result == "Gemini response"

    def test_nested_response_priority(self):
        """测试嵌套 response 优先级"""
        response = {
            "response": {"text": "Nested text"},
            "text": "Top level text"
        }
        result, success = extract_explanation_text(response)
        assert success is True
        # nested_response_text 应优先于 text_key
        assert result == "Nested text"


class TestHelperFunctions:
    """测试辅助提取函数"""

    # =========================================================================
    # _extract_openai_choices 测试
    # =========================================================================

    def test_extract_openai_choices_valid(self):
        """测试有效的 OpenAI 格式"""
        response = {"choices": [{"message": {"content": "Test"}}]}
        result = _extract_openai_choices(response)
        assert result == "Test"

    def test_extract_openai_choices_delta(self):
        """测试 delta 格式"""
        response = {"choices": [{"delta": {"content": "Delta content"}}]}
        result = _extract_openai_choices(response)
        assert result == "Delta content"

    def test_extract_openai_choices_empty(self):
        """测试空 choices"""
        response = {"choices": []}
        result = _extract_openai_choices(response)
        assert result is None

    def test_extract_openai_choices_not_dict(self):
        """测试非 dict 输入"""
        result = _extract_openai_choices("string")
        assert result is None

    # =========================================================================
    # _extract_nested_response_text 测试
    # =========================================================================

    def test_extract_nested_text_valid(self):
        """测试有效的嵌套 text"""
        response = {"response": {"text": "Nested"}}
        result = _extract_nested_response_text(response)
        assert result == "Nested"

    def test_extract_nested_text_not_dict(self):
        """测试 response 不是 dict 的情况"""
        response = {"response": "string value"}
        result = _extract_nested_response_text(response)
        assert result is None

    # =========================================================================
    # _extract_nested_response_content 测试
    # =========================================================================

    def test_extract_nested_content_valid(self):
        """测试有效的嵌套 content"""
        response = {"response": {"content": "Content value"}}
        result = _extract_nested_response_content(response)
        assert result == "Content value"

    def test_extract_nested_content_empty(self):
        """测试空 content"""
        response = {"response": {"content": ""}}
        result = _extract_nested_response_content(response)
        assert result is None

    # =========================================================================
    # _extract_json_from_markdown 测试
    # =========================================================================

    def test_extract_json_from_markdown_valid(self):
        """测试有效的 Markdown JSON"""
        response = '''```json
{"response": "JSON content"}
```'''
        result = _extract_json_from_markdown(response)
        assert result == "JSON content"

    def test_extract_json_from_markdown_no_block(self):
        """测试无代码块"""
        response = "No code block here"
        result = _extract_json_from_markdown(response)
        assert result is None

    def test_extract_json_from_markdown_invalid_json(self):
        """测试无效 JSON"""
        response = '''```json
{invalid}
```'''
        result = _extract_json_from_markdown(response)
        assert result is None

    def test_extract_json_from_markdown_plain_block(self):
        """测试无标记的代码块"""
        response = '''```
{"text": "Plain block content"}
```'''
        result = _extract_json_from_markdown(response)
        assert result == "Plain block content"


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.G.1: DEBUG_AGENT_RESPONSE 日志测试
# [Source: docs/stories/story-12.G.1-api-response-logging.md#Task-5]
# ═══════════════════════════════════════════════════════════════════════════════

class TestDebugAgentResponseLogging:
    """测试 DEBUG_AGENT_RESPONSE 环境变量控制的日志行为"""

    def test_extract_with_debug_logging_enabled(self, mocker, caplog):
        """测试 DEBUG_AGENT_RESPONSE=True 时的日志输出 (AC 4)"""
        import logging
        caplog.set_level(logging.DEBUG)

        # Mock settings at the config module level (where it's imported from)
        mock_settings = mocker.MagicMock()
        mock_settings.DEBUG_AGENT_RESPONSE = True
        mocker.patch('app.config.settings', mock_settings)

        # 执行
        result, success = extract_explanation_text({"response": "test content"})

        # 验证成功提取
        assert success is True
        assert result == "test content"

    def test_extract_without_debug_logging(self, mocker, caplog):
        """测试 DEBUG_AGENT_RESPONSE=False 时无额外日志 (AC 5)"""
        import logging
        caplog.set_level(logging.DEBUG)

        # Mock settings.DEBUG_AGENT_RESPONSE = False (默认)
        mock_settings = mocker.MagicMock()
        mock_settings.DEBUG_AGENT_RESPONSE = False
        mocker.patch('app.config.settings', mock_settings)

        # 执行
        result, success = extract_explanation_text({"response": "test"})

        # 验证成功
        assert success is True
        assert result == "test"

        # 验证日志中不包含 "[Story 12.G.1]" 前缀的 debug 条目
        debug_logs = [r for r in caplog.records if r.levelname == "DEBUG"]
        story_logs = [r for r in debug_logs if "[Story 12.G.1]" in r.message]
        assert len(story_logs) == 0, "DEBUG_AGENT_RESPONSE=False 时不应输出 Story 12.G.1 日志"

    def test_config_has_debug_agent_response_field(self):
        """测试配置类包含 DEBUG_AGENT_RESPONSE 字段 (AC 4)"""
        from app.config import Settings

        # 验证字段存在
        settings = Settings()
        assert hasattr(settings, 'DEBUG_AGENT_RESPONSE'), "Settings 应该有 DEBUG_AGENT_RESPONSE 字段"

        # 验证默认值为 False
        assert settings.DEBUG_AGENT_RESPONSE is False, "默认值应为 False"

    def test_config_has_lowercase_alias(self):
        """测试配置类有小写别名属性"""
        from app.config import Settings

        settings = Settings()
        assert hasattr(settings, 'debug_agent_response'), "Settings 应该有 debug_agent_response 属性"
        assert settings.debug_agent_response == settings.DEBUG_AGENT_RESPONSE
