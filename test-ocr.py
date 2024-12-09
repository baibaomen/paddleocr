#!/usr/bin/env python3

import requests
import base64
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def download_and_convert(image_url, secret_key):
    """
    下载图片并转换为base64
    
    Args:
        image_url: 图片URL
        secret_key: OCR服务认证密钥
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
        headers = {
            "Content-Type": "application/json",
            "X-Secret": secret_key
        }
        data = {
            "image": base64_data
        }
        
        print("正在调用OCR服务...")
        print(f"请求URL: {ocr_url}")
        
        ocr_response = requests.post(ocr_url, headers=headers, json=data)
        
        # 打印响应状态
        print(f"响应状态码: {ocr_response.status_code}")
        
        # 确保响应成功
        ocr_response.raise_for_status()
        
        # 打印结果
        result = ocr_response.json()
        print("\nOCR识别结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"错误详情: {e.response.text}")
        return False
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

if __name__ == "__main__":
    # 从环境变量获取密钥，如果没有则使用默认值
    secret_key = os.getenv('SECRET_KEY', 'key1')
    image_url = "https://api.minio.baibaomen.com/pub/ocr-test.png"
    
    success = download_and_convert(image_url, secret_key)
    exit(0 if success else 1)