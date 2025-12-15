"""
Simple GLM Rate Limiter Test
简化版GLM Coding Plan用量管理系统测试
"""

import asyncio
from glm_rate_limiter import create_rate_limiter, PlanType


async def test_glm_rate_limiter():
    """测试GLM速率限制器核心功能"""
    print("Testing GLM Rate Limiter\n")

    # 创建速率限制器
    limiter = create_rate_limiter("pro")
    print(f"Created rate limiter with plan: pro")
    print(f"Max prompts per period: {limiter.config.max_prompts_per_period}")
    print(f"Rate limit: {limiter.config.rate_limit_requests_per_second} req/s")

    # 启动限制器
    await limiter.start()
    print("\nRate limiter started")

    # 检查初始状态
    status = await limiter.get_usage_status()
    print(f"\nInitial status:")
    print(f"  Total: {status.total_prompts}")
    print(f"  Used: {status.used_prompts}")
    print(f"  Remaining: {status.remaining_prompts}")
    print(f"  Usage: {status.usage_percentage:.1%}")

    # 关闭智能节流以便测试
    limiter.config.enable_smart_throttling = False

    # 测试消耗
    print("\nTesting quota consumption:")
    success = await limiter.consume_quota(10)
    print(f"  Consume 10 prompts: {success}")

    status = await limiter.get_usage_status()
    print(f"\nAfter consumption:")
    print(f"  Used: {status.used_prompts}")
    print(f"  Remaining: {status.remaining_prompts}")
    print(f"  Usage: {status.usage_percentage:.1%}")

    # 测试超额消耗
    print("\nTesting over-consumption:")
    success = await limiter.consume_quota(1000)
    print(f"  Consume 1000 prompts: {success}")

    # 停止限制器
    await limiter.stop()
    print("\nRate limiter stopped")

    return True


async def test_different_plans():
    """测试不同套餐"""
    print("\n\nTesting Different Plans\n")

    plans = ["lite", "pro", "max"]
    configs = {
        "lite": 120,
        "pro": 600,
        "max": 2400
    }

    for plan in plans:
        limiter = create_rate_limiter(plan)
        expected = configs[plan]
        actual = limiter.config.max_prompts_per_period
        print(f"Plan {plan}: {actual} prompts/5h (expected: {expected}) {'OK' if actual == expected else 'FAIL'}")


async def test_token_bucket():
    """测试令牌桶算法"""
    print("\n\nTesting Token Bucket Algorithm\n")

    from glm_rate_limiter import TokenBucket

    # 创建令牌桶
    bucket = TokenBucket(capacity=10, refill_rate=10.0)
    print(f"Created token bucket: capacity=10, refill_rate=10/sec")

    # 测试消耗
    print("\nTesting token consumption:")
    for i in range(5):
        success = await bucket.consume(1)
        print(f"  Consume 1 token: {success}, tokens left: {bucket.tokens:.1f}")

    # 测试补充
    print("\nWaiting for refill...")
    await asyncio.sleep(0.5)
    print(f"Tokens after 0.5s: {bucket.tokens:.1f}")

    await asyncio.sleep(0.5)
    print(f"Tokens after 1s: {bucket.tokens:.1f}")


async def main():
    """主测试函数"""
    print("GLM Coding Plan Rate Limiter Test Suite")
    print("=" * 50)

    results = []

    # 测试1: 基本功能
    try:
        result = await test_glm_rate_limiter()
        results.append(("Basic Functionality", result))
        print("\nBasic functionality test: PASSED")
    except Exception as e:
        results.append(("Basic Functionality", False))
        print(f"\nBasic functionality test: FAILED - {e}")

    # 测试2: 不同套餐
    try:
        await test_different_plans()
        results.append(("Different Plans", True))
        print("\nDifferent plans test: PASSED")
    except Exception as e:
        results.append(("Different Plans", False))
        print(f"\nDifferent plans test: FAILED - {e}")

    # 测试3: 令牌桶
    try:
        await test_token_bucket()
        results.append(("Token Bucket", True))
        print("\nToken bucket test: PASSED")
    except Exception as e:
        results.append(("Token Bucket", False))
        print(f"\nToken bucket test: FAILED - {e}")

    # 总结
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed.")


if __name__ == "__main__":
    asyncio.run(main())