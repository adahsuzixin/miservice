FROM python:3.9-slim

WORKDIR /app

COPY . /app

# 将 .mi.token 文件复制到 /root 目录
COPY .mi.token /root/.mi.token

# 设置环境变量
ENV MI_USER=1261983738
ENV MI_PASS='pu2NN#5sma?9@rz'
ENV MI_DID=636783845

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
