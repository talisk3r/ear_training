FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update && \
    apt-get install -y \
    git \
    libasound2-dev \
    libsdl2-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set bash as default shell
SHELL ["/bin/bash", "-c"]


# Copy and apply the custom bashrc
COPY bashrc /home/${USERNAME}/.bashrc
RUN echo 'if [ -f ~/.bashrc ]; then source ~/.bashrc; fi' >> /home/${USERNAME}/.bash_profile && \
    chown ${USERNAME}:${USERNAME} /home/${USERNAME}/.bashrc /home/${USERNAME}/.bash_profile

# Set workdir
WORKDIR /workspace

# Install Python requirements manager
RUN pip install --upgrade pip setuptools wheel

# Set user
USER ${USERNAME}

# Default to bash shell
CMD [ "bash" ]

