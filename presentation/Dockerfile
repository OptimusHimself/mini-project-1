FROM python:3.12-slim
WORKDIR /app
RUN pip install flask requests
COPY app.py .
EXPOSE 80
CMD ["python", "app.py"]