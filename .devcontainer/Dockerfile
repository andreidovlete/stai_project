# syntax=docker/dockerfile:1
FROM ubuntu:22.04

# Don't generate .pyc files and allow unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Locale setup
RUN apt-get update && apt-get install -y locales \
 && locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Create non-root user `dev`
ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Install essentials
RUN apt-get update && apt-get install -y \
    sudo \
    git \
    bash \
    bash-completion \
    curl \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    graphviz \
 && groupadd --gid $USER_GID $USERNAME \
 && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
 && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
 && chmod 0440 /etc/sudoers.d/$USERNAME \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip \
 && pip3 install --no-cache-dir -r /tmp/requirements.txt \
 && pip3 install --no-cache-dir pdoc

# Switch to non-root user
USER $USERNAME

# Set working directory
WORKDIR /workspaces/stai_project
ENV PYTHONPATH=/workspaces/stai_project

# Expose Flask port
EXPOSE 5000

# Start the Flask app
CMD ["python3","-m", "src.app"]
