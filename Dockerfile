FROM python:3.13-slim-bookworm
ARG INKYPI_REF=2ff58067d05356802d95884c0bb7d8d03d205087
RUN apt-get update && apt-get install -y --no-install-recommends git curl chromium fonts-noto-color-emoji libheif1 && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/fatihak/InkyPi.git /app && cd /app && git checkout "$INKYPI_REF"
WORKDIR /app
RUN pip install --no-cache-dir -r install/requirements-dev.txt && bash install/update_vendors.sh
COPY src /overlay/src
COPY scripts/apply_overlay.py /overlay/scripts/apply_overlay.py
RUN python /overlay/scripts/apply_overlay.py /app
COPY device.json /app/src/config/device.json
EXPOSE 80
CMD ["python", "src/inkypi.py"]
