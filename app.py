from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import os

app = Flask(__name__)

# 初始化PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

@app.route('/ocr', methods=['POST'])
def perform_ocr():
    try:
        # 获取请求参数
        data = request.get_json()
        img_path = data.get('img_path')
        cls = data.get('cls', True)  # 默认为True
        
        # 验证参数
        if not img_path:
            return jsonify({'error': 'img_path is required'}), 400
            
        # 验证文件是否存在
        if not os.path.exists(img_path):
            return jsonify({'error': 'Image file not found'}), 404

        # 执行OCR
        result = ocr.ocr(img_path, cls=cls)
        
        # 格式化结果
        formatted_result = []
        for idx in range(len(result)):
            res = result[idx]
            page_result = []
            for line in res:
                page_result.append({
                    'position': line[0],
                    'text': line[1][0],
                    'confidence': float(line[1][1])  # 转换为float以确保JSON序列化
                })
            formatted_result.append(page_result)

        return jsonify({
            'status': 'success',
            'result': formatted_result
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 