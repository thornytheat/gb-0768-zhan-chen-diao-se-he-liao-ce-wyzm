FROM python:3.12-slim
WORKDIR /studio
COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements-test.txt
COPY . .
ENV PALETTE_SHELF=/data/receipts
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--threads", "4", "app.main:create_app()"]
