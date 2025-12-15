#!/usr/bin/env python3

import torch
print("=== GPU 测试 ===")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device count: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name()}")
    print(f"Memory allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
    print(f"Memory cached: {torch.cuda.memory_reserved() / 1024**2:.2f} MB")
else:
    print("CUDA 不可用")

print("\n=== Whisper 测试 ===")
try:
    import whisper
    print("OpenAI Whisper 加载成功")
    
    # 测试加载模型
    model = whisper.load_model("tiny")
    print(f"模型加载成功: {type(model)}")
    print(f"模型设备: {next(model.parameters()).device}")
    
except Exception as e:
    print(f"Whisper 错误: {e}")

try:
    from faster_whisper import WhisperModel
    print("\nFaster-Whisper 加载成功")
    
    # 测试GPU加速
    model = WhisperModel("tiny", device="cuda", compute_type="float16")
    print("Faster-Whisper GPU模型创建成功")
    
except Exception as e:
    print(f"Faster-Whisper 错误: {e}")

print("\n=== 测试完成 ===") 