"""Local stand-in for Samsung's appliance connectivity check.

Some Samsung appliances (confirmed on the DA_WM_TP1_21_COMMON washer board)
have no NTP client. They set their clock from the reply to

    GET http://info.cspserver.net/api/v1/connect-test

and, without a valid clock, stop reporting cumulative energy. This server
answers that request exactly as Samsung's server does: 200, a Date header,
text/plain, an empty body and no Server header.
"""

import datetime
import http.server
import json
import sys

OPTIONS_PATH = "/data/options.json"


def load_options(path=OPTIONS_PATH):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


class ConnectTestHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    log_requests = True

    def _handle(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        if self.log_requests:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
            print(
                f"{now} {self.client_address[0]} {self.requestline!r} "
                f"Host={self.headers.get('Host')!r}",
                flush=True,
            )
        self.send_response_only(200)
        self.send_header("Date", self.date_time_string())
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

    do_GET = do_HEAD = do_POST = do_PUT = _handle

    def log_message(self, format, *args):  # noqa: A002 - stdlib signature
        pass


def make_server(host="0.0.0.0", port=80, log_requests=True):
    handler = type("Handler", (ConnectTestHandler,), {"log_requests": log_requests})
    return http.server.ThreadingHTTPServer((host, port), handler)


def main():
    options = load_options()
    server = make_server(log_requests=bool(options.get("log_requests", True)))
    print(f"Samsung Clock Responder listening on port {server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
