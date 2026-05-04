FROM docker.m.daocloud.io/library/python:3.12-slim
WORKDIR /srv
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple Flask==3.0.3
COPY internal_app.py .
EXPOSE 7001
CMD ["python", "internal_app.py"]
