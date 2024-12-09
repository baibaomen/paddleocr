# 使用官方的PaddlePaddle GPU镜像作为基础镜像
FROM paddlepaddle/paddle:2.6.2-gpu-cuda12.0-cudnn8.9-trt8.6

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY .env .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install python-dotenv && \
    rm -rf ~/.cache/pip

# 复制应用代码
COPY app.py .

# 暴露端口
EXPOSE 25098

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:25098/health || exit 1

# 启动应用
CMD ["python", "app.py"]