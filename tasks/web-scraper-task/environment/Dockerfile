FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    requests==2.32.3 \
    beautifulsoup4==4.12.3 \
    lxml==5.3.0 \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

# Create logs directory structure
RUN mkdir -p /logs/agent /logs/verifier

CMD ["/bin/bash"]
