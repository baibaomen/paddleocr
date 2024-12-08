# 使用官方的PaddlePaddle GPU镜像作为基础镜像。已测试3.0版本对不完整支持avx指令集的无法使用。
FROM paddlepaddle/paddle:2.6.2-gpu-cuda12.0-cudnn8.9-trt8.6

# 设置工作目录
WORKDIR /app

# 复制requirements.txt和app.py到容器中
COPY requirements.txt .
COPY app.py .

# 安装依赖
RUN pip install -r requirements.txt

# 暴露端口
EXPOSE 25098

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动应用
CMD ["python", "app.py"]