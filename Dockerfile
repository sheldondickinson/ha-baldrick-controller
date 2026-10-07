FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pixeltool ./pixeltool
COPY custom_components/baldrick_controller/esp_api.py ./custom_components/baldrick_controller/esp_api.py
COPY custom_components/baldrick_controller/api.py ./custom_components/baldrick_controller/api.py
RUN touch custom_components/__init__.py custom_components/baldrick_controller/__init__.py
USER 65534:65534
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python","-m","pixeltool.server"]
