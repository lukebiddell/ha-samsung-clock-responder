ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache python3

COPY rootfs/ /

CMD ["python3", "-u", "/usr/bin/samsung_clock_responder.py"]
