FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r npmcp && useradd -r -g npmcp npmcp

COPY pyproject.toml README.md LICENSE ./
COPY nginx_proxy_manager_mcp ./nginx_proxy_manager_mcp
RUN pip install --no-cache-dir .

USER npmcp

CMD ["nginx-proxy-manager-mcp"]
