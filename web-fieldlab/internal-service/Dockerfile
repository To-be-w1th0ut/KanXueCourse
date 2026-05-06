FROM docker.m.daocloud.io/library/python:3.12-slim
WORKDIR /srv
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} Flask==3.0.3
COPY internal_app.py .
EXPOSE 7001
CMD ["python", "internal_app.py"]
