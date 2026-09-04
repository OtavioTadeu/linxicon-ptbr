# Usar imagem oficial do Python, versão slim (mais leve)
FROM python:3.10-slim

# Definir diretório de trabalho dentro do container
WORKDIR /app

# Copiar apenas os arquivos de dependência primeiro (para aproveitar o cache do Docker)
COPY requirements.txt .

# Instalar a versão exclusiva de CPU do PyTorch (para economizar RAM e espaço)
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
# Instalar as demais bibliotecas
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código do projeto para a imagem
COPY . .

# Comando para iniciar o FastAPI (o Cloud Run define a porta dinamicamente na variável $PORT)
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}"]
