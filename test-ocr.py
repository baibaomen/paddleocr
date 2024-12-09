#!/usr/bin/env python3

import requests
import base64
import json

def download_and_convert(image_url):
    """
    下载图片并转换为base64
    """
    try:
        # 下载图片
        print(f"正在下载图片: {image_url}")
        response = requests.get(image_url)
        response.raise_for_status()
        
        # 保存图片
        image_path = "ocr-test.png"
        with open(image_path, "wb") as f:
            f.write(response.content)
        print(f"图片已保存为: {image_path}")
        
        # 转换为base64
        with open(image_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode('utf-8')
        print("图片已转换为base64")
        
        # 调用OCR服务
        ocr_url = "http://localhost:25098/ocr"
        headers = {"Content-Type": "application/json"}
        data = {
            "image": base64_data
        }
        
        print("正在调用OCR服务...")
        ocr_response = requests.post(ocr_url, headers=headers, json=data)
        ocr_response.raise_for_status()
        
        # 打印结果
        result = ocr_response.json()
        print("\nOCR识别结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    image_url = "https://api.minio.baibaomen.com/pub/ocr-test.png"
    download_and_convert(image_url)