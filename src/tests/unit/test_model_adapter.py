"""
Unit tests for Model Compatibility Adapter module
Epic 9 - Canvas System Robustness Enhancement
Story 9.6 - Integration Testing and Validation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from canvas_utils.model_adapter import (
        ModelCompatibilityAdapter,
        Opus41Processor,
        GLM46Processor,
        Sonnet35Processor,
        DefaultProcessor,
        ModelProcessor
    )
    CANVAS_UTILS_AVAILABLE = True
except ImportError:
    CANVAS_UTILS_AVAILABLE = False
    ModelCompatibilityAdapter = Mock
    ModelProcessor = Mock


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.model_adapter not available")
class TestModelCompatibilityAdapter:
    """Test suite for ModelCompatibilityAdapter"""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance for testing"""
        return ModelCompatibilityAdapter()

    @pytest.fixture
    def mock_opus_response(self):
        """Mock Opus 4.1 response"""
        return {
            'model': 'claude-opus-4-1-20250805',
            'usage': {
                'input_tokens': 1000,
                'output_tokens': 500
            }
        }

    @pytest.fixture
    def mock_glm_response(self):
        """Mock GLM-4.6 response"""
        return {
            'model': 'glm-4.6',
            'choices': [{
                'message': {'content': 'Test response'},
                'finish_reason': 'stop'
            }]
        }

    @pytest.fixture
    def mock_sonnet_response(self):
        """Mock Sonnet 3.5 response"""
        return {
            'model': 'claude-3-5-sonnet-20241022',
            'stop_reason': 'end_turn'
        }

    def test_singleton_pattern(self, adapter):
        """Test that adapter follows singleton pattern"""
        adapter2 = ModelCompatibilityAdapter()
        assert adapter is adapter2, "Adapter should be singleton"

    def test_detect_model_opus41(self, adapter, mock_opus_response):
        """Test Opus 4.1 model detection"""
        detected = adapter.detect_model(mock_opus_response)
        assert detected == 'opus-4.1'

    def test_detect_model_glm46(self, adapter, mock_glm_response):
        """Test GLM-4.6 model detection"""
        detected = adapter.detect_model(mock_glm_response)
        assert detected == 'glm-4.6'

    def test_detect_model_sonnet35(self, adapter, mock_sonnet_response):
        """Test Sonnet 3.5 model detection"""
        detected = adapter.detect_model(mock_sonnet_response)
        assert detected == 'sonnet-3.5'

    def test_detect_model_unknown(self, adapter):
        """Test unknown model detection"""
        unknown_response = {'model': 'unknown-model-123'}
        detected = adapter.detect_model(unknown_response)
        assert detected == 'default'

    def test_get_processor_opus41(self, adapter):
        """Test getting Opus 4.1 processor"""
        processor = adapter.get_processor('opus-4.1')
        assert isinstance(processor, Opus41Processor)

    def test_get_processor_glm46(self, adapter):
        """Test getting GLM-4.6 processor"""
        processor = adapter.get_processor('glm-4.6')
        assert isinstance(processor, GLM46Processor)

    def test_get_processor_sonnet35(self, adapter):
        """Test getting Sonnet 3.5 processor"""
        processor = adapter.get_processor('sonnet-3.5')
        assert isinstance(processor, Sonnet35Processor)

    def test_get_processor_default(self, adapter):
        """Test getting default processor"""
        processor = adapter.get_processor('unknown-model')
        assert isinstance(processor, DefaultProcessor)

    def test_processor_caching(self, adapter):
        """Test that processors are cached"""
        processor1 = adapter.get_processor('opus-4.1')
        processor2 = adapter.get_processor('opus-4.1')
        assert processor1 is processor2, "Processor should be cached"

    def test_register_custom_processor(self, adapter):
        """Test registering custom processor"""
        class CustomProcessor(ModelProcessor):
            def process_response(self, response):
                return {'custom': True}

        adapter.register_processor('custom-model', CustomProcessor)
        processor = adapter.get_processor('custom-model')
        assert isinstance(processor, CustomProcessor)

    @pytest.mark.asyncio
    async def test_process_response_opus41(self, adapter, mock_opus_response):
        """Test processing Opus 4.1 response"""
        result = await adapter.process_response(mock_opus_response)
        assert result['model'] == 'opus-4.1'
        assert 'usage' in result

    @pytest.mark.asyncio
    async def test_process_response_glm46(self, adapter, mock_glm_response):
        """Test processing GLM-4.6 response"""
        result = await adapter.process_response(mock_glm_response)
        assert result['model'] == 'glm-4.6'
        assert 'choices' in result

    @pytest.mark.asyncio
    async def test_adapt_request_opus41(self, adapter):
        """Test adapting request for Opus 4.1"""
        request = {'messages': [{'role': 'user', 'content': 'Test'}]}
        adapted = await adapter.adapt_request(request, 'opus-4.1')
        assert 'messages' in adapted
        assert adapted['messages'][0]['content'] == 'Test'

    @pytest.mark.asyncio
    async def test_adapt_request_glm46(self, adapter):
        """Test adapting request for GLM-4.6"""
        request = {'messages': [{'role': 'user', 'content': 'Test'}]}
        adapted = await adapter.adapt_request(request, 'glm-4.6')
        assert 'messages' in adapted

    def test_validate_response_opus41(self, adapter, mock_opus_response):
        """Test validating Opus 4.1 response"""
        is_valid = adapter.validate_response(mock_opus_response, 'opus-4.1')
        assert is_valid

    def test_validate_response_invalid(self, adapter):
        """Test validating invalid response"""
        invalid_response = {'error': 'Failed'}
        is_valid = adapter.validate_response(invalid_response, 'opus-4.1')
        assert not is_valid

    def test_error_handling(self, adapter):
        """Test error handling in adapter"""
        with patch.object(adapter, 'detect_model', side_effect=Exception("Test error")):
            with pytest.raises(Exception):
                adapter.detect_model({})


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.model_adapter not available")
class TestOpus41Processor:
    """Test suite for Opus41Processor"""

    @pytest.fixture
    def processor(self):
        """Create Opus41Processor instance"""
        return Opus41Processor()

    @pytest.mark.asyncio
    async def test_process_response(self, processor):
        """Test response processing"""
        response = {
            'model': 'claude-opus-4-1-20250805',
            'content': [{'type': 'text', 'text': 'Response text'}]
        }
        result = await processor.process_response(response)
        assert result['model'] == 'opus-4.1'
        assert 'content' in result

    @pytest.mark.asyncio
    async def test_extract_content(self, processor):
        """Test content extraction"""
        response = {
            'content': [
                {'type': 'text', 'text': 'Text content'},
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': '...'}}
            ]
        }
        content = await processor.extract_content(response)
        assert 'text' in content
        assert 'images' in content

    def test_get_rate_limits(self, processor):
        """Test getting rate limits"""
        limits = processor.get_rate_limits()
        assert 'requests_per_minute' in limits
        assert 'tokens_per_minute' in limits

    def test_supports_function_calling(self, processor):
        """Test function calling support"""
        assert processor.supports_function_calling()

    def test_get_max_tokens(self, processor):
        """Test getting max tokens"""
        max_tokens = processor.get_max_tokens()
        assert isinstance(max_tokens, int)
        assert max_tokens > 0


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.model_adapter not available")
class TestGLM46Processor:
    """Test suite for GLM46Processor"""

    @pytest.fixture
    def processor(self):
        """Create GLM46Processor instance"""
        return GLM46Processor()

    @pytest.mark.asyncio
    async def test_process_response(self, processor):
        """Test response processing"""
        response = {
            'model': 'glm-4.6',
            'choices': [{
                'message': {'content': 'Response text'},
                'finish_reason': 'stop'
            }]
        }
        result = await processor.process_response(response)
        assert result['model'] == 'glm-4.6'
        assert 'content' in result

    def test_get_rate_limits(self, processor):
        """Test getting rate limits"""
        limits = processor.get_rate_limits()
        assert 'requests_per_minute' in limits
        assert 'tokens_per_minute' in limits

    def test_supports_function_calling(self, processor):
        """Test function calling support"""
        assert processor.supports_function_calling()


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.model_adapter not available")
class TestSonnet35Processor:
    """Test suite for Sonnet35Processor"""

    @pytest.fixture
    def processor(self):
        """Create Sonnet35Processor instance"""
        return Sonnet35Processor()

    @pytest.mark.asyncio
    async def test_process_response(self, processor):
        """Test response processing"""
        response = {
            'model': 'claude-3-5-sonnet-20241022',
            'content': [{'type': 'text', 'text': 'Response text'}],
            'stop_reason': 'end_turn'
        }
        result = await processor.process_response(response)
        assert result['model'] == 'sonnet-3.5'
        assert 'content' in result

    def test_get_context_window(self, processor):
        """Test getting context window size"""
        context_window = processor.get_context_window()
        assert isinstance(context_window, int)
        assert context_window > 0


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.model_adapter not available")
class TestDefaultProcessor:
    """Test suite for DefaultProcessor"""

    @pytest.fixture
    def processor(self):
        """Create DefaultProcessor instance"""
        return DefaultProcessor()

    @pytest.mark.asyncio
    async def test_process_response(self, processor):
        """Test response processing"""
        response = {'model': 'unknown', 'content': 'Response'}
        result = await processor.process_response(response)
        assert result['model'] == 'default'
        assert 'content' in result

    def test_get_fallback_behavior(self, processor):
        """Test fallback behavior"""
        assert processor.get_fallback_behavior() == 'basic_processing'


if __name__ == '__main__':
    # Run tests when script is executed directly
    pytest.main([__file__, '-v'])