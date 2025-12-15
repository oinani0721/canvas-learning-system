#!/usr/bin/env python3

print("Testing imports...")

try:
    import torch
    print("✅ PyTorch imported successfully")
    print(f"CUDA available: {torch.cuda.is_available()}")
except Exception as e:
    print(f"❌ PyTorch error: {e}")

try:
    import whisper
    print("✅ Whisper imported successfully")
except Exception as e:
    print(f"❌ Whisper error: {e}")

try:
    from faster_whisper import WhisperModel
    print("✅ Faster-Whisper imported successfully")
except Exception as e:
    print(f"❌ Faster-Whisper error: {e}")

try:
    from flask import Flask
    print("✅ Flask imported successfully")
except Exception as e:
    print(f"❌ Flask error: {e}")

print("All imports tested!") 