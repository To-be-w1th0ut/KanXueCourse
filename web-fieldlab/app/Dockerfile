FROM docker.m.daocloud.io/library/python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
ARG PIP_INDEX_URL=https://pypi.org/simple

COPY requirements.txt ./
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} -r requirements.txt

COPY . .
EXPOSE 5000
CMD ["python", "run.py"]
