FROM python:3.12-slim
WORKDIR /app
RUN pip install flask
COPY app.py .
VOLUME /data
EXPOSE 5002
CMD ["python", "app.py"]