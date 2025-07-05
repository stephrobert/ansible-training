# Stage 1: Build stage avec tous les outils de build
FROM python:3.13-slim-bookworm AS builder
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

# Installation des dépendances de build et Git
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Création de l'environnement virtuel
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install ansible>=2.18 ansible-lint>=v25.6.1 pytest>=8.4.1 pytest-testinfra>=6.0.0

# Stage 2: Image finale minimale
FROM python:3.13-slim-bookworm AS final

# Installation de Git uniquement (sans les dépendances de build)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Création de l'utilisateur lab-user
RUN useradd -m -s /bin/bash lab-user

# Copie de l'environnement virtuel depuis le stage builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Changement de propriétaire pour l'environnement virtuel
RUN chown -R lab-user:lab-user /opt/venv

# Basculement vers l'utilisateur lab-user
USER lab-user
RUN git clone https://github.com/stephrobert/ansible-training /home/lab-user/ansible-training
WORKDIR /home/lab-user/ansible-training

# Définir le point d'entrée
CMD ["/bin/bash"]