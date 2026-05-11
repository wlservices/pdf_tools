# Usamos uma imagem Python oficial baseada em Debian (slim para ser mais leve)
FROM python:3.10-slim

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
  ghostscript \
  libreoffice \
  # Dependências comuns para renderização e PDF
  libmagic1 \
  fonts-liberation \
  && apt-get clean \
  # Remove listas do apt para reduzir o tamanho da imagem
  && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de dependências do Python
COPY requirements.txt .

# Instala as bibliotecas Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código do seu projeto
COPY . .

# Cria as pastas que o seu código usa para upload e conversão
RUN mkdir -p uploads converted

# Comando para rodar a aplicação (ajuste para o seu arquivo principal)
CMD ["python", "app.py"]