FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY services/tools/timeseries_forecaster/app.py /app/app.py
EXPOSE 9093
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9093"]