from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import requests
import base64
import logging
import time
from datetime import datetime
from io import BytesIO
from PIL import Image

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化PaddleOCR
logger.info("Initializing PaddleOCR models...")
ocrCn = PaddleOCR(use_angle_cls=True, lang='ch')
ocrEn = PaddleOCR(use_angle_cls=True, lang='en')
logger.info("PaddleOCR models initialized successfully")

def calculate_slice_params(image_width, image_height):
    """
    根据图片尺寸计算合适的slice参数
    """
    horizontal_stride = max(300, min(800, image_width // 3))
    vertical_stride = max(300, min(800, image_height // 3))
    
    merge_x_thres = 12
    merge_y_thres = 12
    
    return {
        "horizontal_stride": horizontal_stride,
        "vertical_stride": vertical_stride,
        "merge_x_thres": merge_x_thres,
        "merge_y_thres": merge_y_thres
    }

def get_image_from_url(img_url):
    """
    从URL获取图片，返回BytesIO对象
    """
    start_time = time.time()
    logger.info(f"Starting to download image from: {img_url}")
    
    response = requests.get(img_url, stream=True)
    response.raise_for_status()
    
    image_data = BytesIO(response.content)
    
    download_time = time.time() - start_time
    logger.info(f"Image downloaded (took {download_time:.2f}s)")
    
    return image_data

def get_image_from_base64(base64_string):
    """
    从base64字符串获取图片，返回BytesIO对象
    """
    start_time = time.time()
    logger.info("Processing base64 image")
    
    # 移除base64头部信息（如果存在）
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    image_data = BytesIO(base64.b64decode(base64_string))
    
    process_time = time.time() - start_time
    logger.info(f"Base64 image processed (took {process_time:.2f}s)")
    
    return image_data

@app.route('/ocr', methods=['POST'])
def perform_ocr():
    request_start_time = time.time()
    logger.info("Received OCR request")
    
    try:
        data = request.get_json()
        logger.info("Request received")

        # 获取语言设置
        lang = data.get('lang', 'ch')
        ocr = ocrEn if lang == 'en' else ocrCn
        
        img_url = data.get('img_url')
        if not img_url:
            raise ValueError("Missing img_url in request")

        # 处理图片输入
        if img_url.startswith(('http://', 'https://')):
            image_data = get_image_from_url(img_url)
        else:
            # 假设非URL的输入是base64编码
            image_data = get_image_from_base64(img_url)

        # 获取图片尺寸
        logger.info("Reading image dimensions")
        image_start_time = time.time()
        with Image.open(image_data) as img:
            width, height = img.size
        logger.info(f"Image dimensions: {width}x{height}")

        # 重置文件指针到开始位置
        image_data.seek(0)

        # 计算slice参数
        if width > 2000 or height > 2000:
            slice_config = data.get('slice', calculate_slice_params(width, height))
            logger.info(f"Using slice config: {slice_config}")
        else:
            slice_config = data.get('slice', {})
            logger.info("No slice config needed")

        # 执行OCR
        logger.info("Starting OCR processing")
        ocr_start_time = time.time()
        result = ocr.ocr(image_data, cls=data.get('cls', True), slice=slice_config)
        ocr_time = time.time() - ocr_start_time
        logger.info(f"OCR processing completed in {ocr_time:.2f}s")

        # 格式化结果
        formatted_result = []
        for idx in range(len(result)):
            res = result[idx]
            page_result = []
            for line in res:
                page_result.append({
                    'position': line[0],
                    'text': line[1][0],
                    'confidence': float(line[1][1])
                })
            formatted_result.append(page_result)

        total_time = time.time() - request_start_time
        response_data = {
            'status': 'success',
            'result': formatted_result,
            'processing_time': {
                'total': f"{total_time:.2f}s",
                'ocr': f"{ocr_time:.2f}s"
            }
        }
        
        logger.info(f"Request completed in {total_time:.2f}s")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    logger.info("Starting OCR service on port 25098")
    app.run(host='0.0.0.0', port=25098) 