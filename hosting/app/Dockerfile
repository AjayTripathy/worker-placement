FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY hosting ./hosting
COPY officekit ./officekit
COPY officekit_ai ./officekit_ai
RUN useradd --uid 10001 --create-home appuser
USER 10001
CMD ["sh", "-c", "exec uvicorn hosting.app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8080} --no-access-log --workers 1"]
