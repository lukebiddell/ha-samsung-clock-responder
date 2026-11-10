ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache python3

COPY rootfs/ /

HEALTHCHECK --interval=60s --timeout=5s --start-period=10s \
  CMD ["python3", "/usr/bin/samsung_clock_responder.py", "--healthcheck"]

CMD ["python3", "-u", "/usr/bin/samsung_clock_responder.py"]
