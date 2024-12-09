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

# Paddleocr supports Chinese, English, French, German, Korean and Japanese
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

def main():
    print("\nOCR服务已启动. 按Ctrl+C退出.\n")
    while True:
        try:
            img_input = input("请输入图片URL或base64编码 (或按Ctrl+C退出): ")
            if not img_input.strip():
                print("[WARN] 输入不能为空")
                continue

            # 获取图片数据
            try:
                content = get_image_content(img_input)
            except Exception as e:
                print(f"[ERROR] 图片获取失败: {str(e)}")
                continue

            # 处理OCR
            try:
                result = process_image(content)

                # 打印结果
                print("\nOCR结果:")
                if not result or len(result) == 0:
                    print("未检测到文本")
                    continue

                print(json.dumps(result, ensure_ascii=False, indent=2))

                for idx in range(len(result)):
                    res = result[idx]
                    if not res:  # 检查是否为空列表
                        continue
                    for line in res:
                        print(line[1][0])

            except Exception as e:
                print(f"[ERROR] OCR处理失败: {str(e)}")
                if str(e).strip():  # 只在有错误信息时打印堆栈
                    print(traceback.format_exc())
                continue

        except KeyboardInterrupt:
            print("\n程序已退出")
            break
        except Exception as e:
            print(f"[ERROR] 发生未知错误: {str(e)}")
            print(traceback.format_exc())
            continue

if __name__ == "__main__":
    main()
