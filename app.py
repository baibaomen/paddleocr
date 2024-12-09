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
            response = requests.get(img_input, stream=True)
            response.raise_for_status()
            content = response.content
            print(f"[INFO] 图片下载完成 (耗时 {time.time() - start_time:.2f}秒)")
            
        return content
    except Exception as e:
        print(f"[ERROR] 图片获取失败: {str(e)}")
        raise

def process_image(content):
    """
    处理图片并执行OCR
    """
    try:
        ocr_start_time = time.time()
        print("[INFO] 开始OCR处理")

        # 转换为PIL Image
        image = Image.open(BytesIO(content))
        width, height = image.size
        print(f"[INFO] 图片尺寸: {width}x{height}")

        # 转换为numpy数组
        image_array = np.array(image)

        result = ocr.ocr(image_array)

        if result is None:
            raise ValueError("OCR未返回结果")

        ocr_time = time.time() - ocr_start_time
        print(f"[INFO] OCR处理完成 (耗时 {ocr_time:.2f}秒)")
        return result

    except Exception as e:
        print(f"[ERROR] OCR处理错误: {str(e)}")
        raise

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    """
    OCR服务HTTP接口
    请求体格式: { "image": "图片URL或base64编码" }
    """
    try:
        # 获取并验证请求数据
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': '请求体必须包含image字段'
            }), 400

        img_input = data['image']
        if not img_input.strip():
            return jsonify({
                'success': False,
                'error': 'image不能为空'
            }), 400

        # 获取图片内容
        content = get_image_content(img_input)
        
        # 执行OCR处理
        result = process_image(content)
        
        # 格式化OCR结果
        text_results = []
        if result and len(result) > 0:
            for idx in range(len(result)):
                res = result[idx]
                if not res:
                    continue
                for line in res:
                    text_results.append(line[1][0])

        return jsonify({
            'success': True,
            'raw_result': result,
            'text_results': text_results
        })

    except Exception as e:
        print(f"[ERROR] 处理失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

def main():
    print("\nOCR HTTP服务已启动在 http://0.0.0.0:25098\n")
    print("API接口:")
    print("1. POST /ocr - OCR识别")
    print("2. GET /health - 健康检查")
    app.run(host='0.0.0.0', port=25098)

if __name__ == "__main__":
    main()