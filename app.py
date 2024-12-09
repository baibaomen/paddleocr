from flask import Flask, request, jsonify, make_response
from paddleocr import PaddleOCR
import requests
import base64
import time
import traceback
import numpy as np
from datetime import datetime
from io import BytesIO
from PIL import Image
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取配置并处理多个密钥
SECRET_KEYS = [key.strip() for key in os.getenv('SECRET_KEY', '').split(',') if key.strip()]
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')
MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', 10485760))  # 默认10MB

# 初始化Flask应用
app = Flask(__name__)
app.json.ensure_ascii = False

# 初始化PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch', det_limit_type='min')

def is_base64_image(s):
    """检查字符串是否为base64编码的图片"""
    return isinstance(s, str) and (
        s.startswith('data:image/') or
        (len(s) % 4 == 0 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in s))
    )

def verify_secret(request):
    """验证请求密钥
    
    支持从以下位置获取密钥：
    1. 请求头 X-Secret
    2. POST参数 secret
    
    配置支持多个密钥（逗号分隔），匹配其中之一即可
    """
    # 从请求头获取
    auth_header = request.headers.get('X-Secret')
    
    # 从POST参数获取
    auth_param = None
    if request.is_json:
        auth_param = request.json.get('secret')
    
    # 验证密钥
    secret = auth_header or auth_param
    if not secret:
        raise Exception('缺少认证密钥')
    if not any(secret == valid_key for valid_key in SECRET_KEYS):
        raise Exception('认证密钥无效')

def get_image_content(img_input):
    """获取图片内容，支持URL和base64"""
    try:
        start_time = time.time()

        if is_base64_image(img_input):
            print("[INFO] 检测到base64编码图片")
            # 如果包含data URI scheme，移除它
            if img_input.startswith('data:image/'):
                base64_data = img_input.split(',')[1]
            else:
                base64_data = img_input

            content = base64.b64decode(base64_data)
            print(f"[INFO] base64解码完成 (耗时 {time.time() - start_time:.2f}秒)")
        else:
            print(f"[INFO] 开始下载图片: {img_input}")
            response = requests.get(img_input, timeout=10)
            response.raise_for_status()
            content = response.content
            print(f"[INFO] 图片下载完成 (耗时 {time.time() - start_time:.2f}秒)")

        return content
    except Exception as e:
        raise Exception(f"获取图片失败: {str(e)}")

def process_image(image_content):
    """处理图片内容并进行OCR识别"""
    try:
        start_time = time.time()

        # 将图片内容转换为PIL Image对象
        image = Image.open(BytesIO(image_content))

        # 将图片转换为RGB模式（如果需要）
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 将PIL Image转换为numpy数组
        img_array = np.array(image)

        print(f"[INFO] 图片预处理完成 (耗时 {time.time() - start_time:.2f}秒)")

        # 执行OCR识别
        start_time = time.time()
        result = ocr.ocr(img_array, cls=True)
        print(f"[INFO] OCR识别完成 (耗时 {time.time() - start_time:.2f}秒)")

        return result
    except Exception as e:
        raise Exception(f"OCR处理失败: {str(e)}")

def get_api_docs(request):
    """生成API文档"""
    host = request.headers.get('Host', 'localhost:25098')
    scheme = request.headers.get('X-Forwarded-Proto', 'http')
    base_url = f"{scheme}://{host}"
    
    return f"""
OCR HTTP服务

服务地址: {base_url}

API接口:
POST /ocr - OCR识别
   请求体格式: {{ "image": "图片URL或base64编码", "secret": "密钥" }}
   或在请求头中添加 X-Secret: 密钥

   示例:
   curl -X POST {base_url}/ocr \\
     -H "Content-Type: application/json" \\
     -H "X-Secret: your-secret-key" \\
     -d '{{"image": "图片URL或base64编码"}}'

注意事项:
- 支持图片URL或base64编码
- 图片大小限制: {MAX_IMAGE_SIZE/1024/1024:.1f}MB
- 支持中文识别
- 返回JSON格式数据
"""

@app.after_request
def after_request(response):
    """设置响应头"""
    if response.mimetype == 'application/json':
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/')
def index():
    """根路径显示API文档"""
    docs = get_api_docs(request)
    response = make_response(docs)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    """OCR识别接口"""
    try:
        # 验证密钥
        verify_secret(request)

        # 获取请求数据
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': '请求数据必须包含image字段'
            }), 400

        img_input = data['image']
        if not img_input:
            return jsonify({
                'success': False,
                'error': 'image字段不能为空'
            }), 400

        # 检查图片大小
        if is_base64_image(img_input):
            img_size = len(base64.b64decode(img_input.split(',')[-1]))
            if img_size > MAX_IMAGE_SIZE:
                return jsonify({
                    'success': False,
                    'error': f'图片大小超过限制 ({MAX_IMAGE_SIZE/1024/1024:.1f}MB)'
                }), 400

        start_time = time.time()

        # 获取图片内容
        content = get_image_content(img_input)

        # 执行OCR处理
        result = process_image(content)

        # 格式化OCR结果
        formatted_result = []
        text_results = []

        if result and len(result) > 0:
            for page in result:
                page_result = []
                for line in page:
                    coords = line[0]
                    text = line[1][0]
                    confidence = line[1][1]

                    page_result.append({
                        'coordinates': coords,
                        'text': text,
                        'confidence': confidence
                    })
                    text_results.append(text)
                formatted_result.append(page_result)

        process_time = time.time() - start_time

        response = make_response(
            jsonify({
                'success': True,
                'raw_result': formatted_result,
                'text_results': text_results,
                'process_time': f"{process_time:.2f}s"
            })
        )
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        print(f"[ERROR] 处理失败: {str(e)}")
        print(traceback.format_exc())
        error_response = make_response(
            jsonify({
                'success': False,
                'error': str(e),
                'error_type': e.__class__.__name__
            }), 
            500
        )
        return error_response

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'OCR Service'
    })

def main():
    print("\nOCR HTTP服务已启动在 http://0.0.0.0:25098")
    app.run(host='0.0.0.0', port=25098)

if __name__ == "__main__":
    main()