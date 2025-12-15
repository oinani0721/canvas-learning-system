#!/usr/bin/env python3

import os
import tempfile
from flask import Flask, request, render_template_string, jsonify, send_file
from werkzeug.utils import secure_filename
import whisper
from faster_whisper import WhisperModel

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# 全局模型变量
whisper_model = None
faster_model = None

def init_models():
    global whisper_model, faster_model
    try:
        print("正在加载 Whisper 模型...")
        whisper_model = whisper.load_model("base", device="cuda")
        print("✅ OpenAI Whisper 模型加载成功")
        
        faster_model = WhisperModel("base", device="cuda", compute_type="float16")
        print("✅ Faster-Whisper 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Whisper 视频转录工具</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { 
            color: #333; 
            text-align: center;
            margin-bottom: 30px;
        }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            background-color: #fafafa;
        }
        .upload-area:hover {
            border-color: #007bff;
            background-color: #f0f8ff;
        }
        input[type="file"] {
            margin: 10px 0;
        }
        select, button {
            padding: 10px 20px;
            margin: 10px 5px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            background-color: #007bff;
            color: white;
            cursor: pointer;
            border: none;
        }
        button:hover {
            background-color: #0056b3;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        .progress {
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-bar {
            height: 100%;
            background-color: #007bff;
            width: 0%;
            transition: width 0.3s ease;
        }
        .error {
            color: #dc3545;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .success {
            color: #155724;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .gpu-status {
            background-color: #e8f5e8;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Whisper GPU 视频转录工具</h1>
        
        <div class="gpu-status">
            <strong>🚀 GPU 状态: {{ gpu_status }}</strong>
        </div>
        
        <div class="upload-area">
            <h3>📁 选择音频/视频文件</h3>
            <input type="file" id="fileInput" accept="audio/*,video/*" />
            <br>
            <small>支持格式: MP3, WAV, MP4, AVI, MKV 等</small>
        </div>
        
        <div style="text-align: center;">
            <label for="model">选择模型:</label>
            <select id="model">
                <option value="faster">Faster-Whisper (推荐)</option>
                <option value="openai">OpenAI Whisper</option>
            </select>
            
            <label for="language">语言:</label>
            <select id="language">
                <option value="auto">自动检测</option>
                <option value="zh">中文</option>
                <option value="en">英语</option>
                <option value="ja">日语</option>
                <option value="ko">韩语</option>
                <option value="fr">法语</option>
                <option value="de">德语</option>
                <option value="es">西班牙语</option>
            </select>
            
            <br><br>
            <button onclick="startTranscription()" id="transcribeBtn">🎯 开始转录</button>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        function startTranscription() {
            const fileInput = document.getElementById('fileInput');
            const model = document.getElementById('model').value;
            const language = document.getElementById('language').value;
            const btn = document.getElementById('transcribeBtn');
            const result = document.getElementById('result');
            
            if (!fileInput.files[0]) {
                alert('请先选择一个文件！');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('model', model);
            formData.append('language', language);
            
            btn.disabled = true;
            btn.textContent = '🔄 转录中...';
            
            result.innerHTML = `
                <div class="loading">
                    <h3>⏳ 正在处理文件，请稍候...</h3>
                    <div class="progress">
                        <div class="progress-bar" style="width: 10%;"></div>
                    </div>
                    <p>使用 GPU 加速中...</p>
                </div>
            `;
            
            fetch('/transcribe', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                btn.disabled = false;
                btn.textContent = '🎯 开始转录';
                
                if (data.success) {
                    result.innerHTML = `
                        <div class="success">
                            <h3>✅ 转录完成！</h3>
                            <p><strong>处理时间:</strong> ${data.processing_time}秒</p>
                            <p><strong>检测语言:</strong> ${data.detected_language || '未知'}</p>
                        </div>
                        <div class="result">
                            <h4>📝 转录结果:</h4>
                            <div style="background: white; padding: 15px; border-radius: 5px; white-space: pre-wrap; line-height: 1.6;">
${data.text}
                            </div>
                        </div>
                    `;
                } else {
                    result.innerHTML = `
                        <div class="error">
                            <h3>❌ 转录失败</h3>
                            <p>${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                btn.disabled = false;
                btn.textContent = '🎯 开始转录';
                result.innerHTML = `
                    <div class="error">
                        <h3>❌ 网络错误</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    # 检查GPU状态
    import torch
    if torch.cuda.is_available():
        gpu_status = f"✅ {torch.cuda.get_device_name()} 已就绪"
    else:
        gpu_status = "❌ GPU 不可用，将使用 CPU"
    
    return render_template_string(HTML_TEMPLATE, gpu_status=gpu_status)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    import time
    start_time = time.time()
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        file = request.files['file']
        model_type = request.form.get('model', 'faster')
        language = request.form.get('language', 'auto')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        # 保存临时文件
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        print(f"开始转录文件: {filename}")
        print(f"使用模型: {model_type}")
        
        result_text = ""
        detected_language = "auto"
        
        try:
            if model_type == 'faster' and faster_model:
                print("使用 Faster-Whisper 进行转录...")
                segments, info = faster_model.transcribe(
                    temp_path, 
                    language=None if language == 'auto' else language
                )
                result_text = ' '.join(segment.text for segment in segments)
                detected_language = info.language
                
            elif model_type == 'openai' and whisper_model:
                print("使用 OpenAI Whisper 进行转录...")
                result = whisper_model.transcribe(
                    temp_path,
                    language=None if language == 'auto' else language
                )
                result_text = result["text"]
                detected_language = result.get("language", "unknown")
            
            else:
                raise Exception("模型未初始化")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        processing_time = round(time.time() - start_time, 2)
        print(f"转录完成，耗时: {processing_time}秒")
        
        return jsonify({
            'success': True,
            'text': result_text.strip(),
            'detected_language': detected_language,
            'processing_time': processing_time
        })
        
    except Exception as e:
        print(f"转录错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🚀 正在启动 Whisper Web 服务...")
    init_models()
    print("🌐 Web 界面启动中...")
    print("📍 访问地址: http://localhost:8082")
    app.run(host='0.0.0.0', port=8082, debug=False) 