FROM python:3.12-slim

WORKDIR /app

# Install shared event schemas (must come before service install)
COPY shared/ /shared/
RUN pip install --no-cache-dir /shared/

# Install service and its dependencies
COPY services/order-api/ .
RUN pip install --no-cache-dir .

CMD ["uvicorn", "order_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
