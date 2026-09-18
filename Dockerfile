FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup -S bgw && adduser -S -G bgw bgw

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps .

USER bgw
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD ["wget", "-qO-", "-T", "5", "http://127.0.0.1:8080/healthz"]

ENTRYPOINT ["bgw-probe"]
CMD ["serve"]
