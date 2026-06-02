FROM python:3.12-slim

WORKDIR /app

# Install shared event schemas
COPY shared/ /shared/
RUN pip install --no-cache-dir /shared/

# Install service and its dependencies
COPY services/inventory-service/ .
RUN pip install --no-cache-dir .

CMD ["python", "-m", "inventory_service.main"]