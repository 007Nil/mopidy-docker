FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-gi \
    gobject-introspection \
    libglib2.0-dev \
    libcairo2-dev \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-alsa \
    libasound2 \
    gcc \
    pkg-config \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY mopidy-requirements.txt .
RUN pip install --no-cache-dir -r mopidy-requirements.txt


RUN pip install --no-cache-dir \
    "mopidy~=3.4" \
    "mopidy-local~=3.3"


RUN mkdir -p /config /data /cache /music

ARG AUDIO_GID=29
ARG USER_ID=1000

RUN groupadd -g ${AUDIO_GID} audio || true \
 && useradd -m -u ${USER_ID} -g audio mopidy \
 && usermod -aG audio mopidy \
 && chown -R mopidy:audio /config /data /cache /music

USER mopidy

EXPOSE 6680 6600

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
