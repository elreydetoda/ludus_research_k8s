FROM python:3.11-slim
RUN pip install flask
RUN apt-get update && apt-get install -y iputils-ping curl wget
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]