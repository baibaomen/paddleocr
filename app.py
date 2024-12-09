from flask import Flask, request, jsonify
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

# 初始化Flask应用
app = Flask(__name__)

# 初始化PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch', det_limit_type='min')

def is_base64_image(s):
    """
    检查字符串是否为base64编码的图片
    """
    return isinstance(s, str) and (
        s.startswith('data:image/') or
        (len(s) % 4 == 0 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in s))
    )

def get_image_content(img_input):
    """
    获取图片内容，支持URL和base64
    """
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
    """
    处理图片内容并进行OCR识别
    """
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

@app.after_request
def after_request(response):
    if response.mimetype == 'application/json':
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    """
    OCR识别接口
    """
    try:
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

        return jsonify({
            'success': True,
            'raw_result': formatted_result,
            'text_results': text_results,
            'process_time': f"{process_time:.2f}s"
        })

    except Exception as e:
        print(f"[ERROR] 处理失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': e.__class__.__name__
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'OCR Service'
    })

def main():
    print("\nOCR HTTP服务已启动在 http://0.0.0.0:25098\n")
    print("API接口:")
    print("1. POST /ocr - OCR识别")
    print("   请求体格式: { \"image\": \"图片URL或base64编码\" }")
    print("2. GET /health - 健康检查")
    app.run(host='0.0.0.0', port=25098)

if __name__ == "__main__":
    main()
