import contextlib
import email.utils
import importlib.util
import io
import json
import pathlib
import socket
import tempfile
import threading
import time
import unittest

SCRIPT = (
    pathlib.Path(__file__).resolve().parent.parent
    / "samsung_clock_responder/rootfs/usr/bin/samsung_clock_responder.py"
)
spec = importlib.util.spec_from_file_location("responder", SCRIPT)
responder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(responder)

# The appliance's request, byte for byte as captured.
CONNECT_TEST = b"GET /api/v1/connect-test HTTP/1.1\r\nHost: info.cspserver.net\r\n\r\n"


def parse_response(raw):
    head, _, body = raw.partition(b"\r\n\r\n")
    lines = head.decode("latin-1").split("\r\n")
    headers = {}
    for line in lines[1:]:
        name, _, value = line.partition(":")
        headers[name.strip()] = value.strip()
    return lines[0], headers, body


class ResponderTest(unittest.TestCase):
    def start(self, log_requests=False):
        server = responder.make_server("127.0.0.1", 0, log_requests=log_requests)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server.server_port

    def request(self, port, payload=CONNECT_TEST):
        with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
            s.sendall(payload)
            s.shutdown(socket.SHUT_WR)
            chunks = []
            while chunk := s.recv(4096):
                chunks.append(chunk)
        return b"".join(chunks)

    def test_reply_matches_samsung_server(self):
        port = self.start()
        status, headers, body = parse_response(self.request(port))
        self.assertEqual(status, "HTTP/1.1 200 OK")
        self.assertEqual(
            list(headers), ["Date", "Content-Type", "Content-Length", "Connection"]
        )
        self.assertEqual(headers["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(headers["Content-Length"], "0")
        self.assertEqual(headers["Connection"], "keep-alive")
        self.assertEqual(body, b"")

    def test_date_header_is_current_utc(self):
        port = self.start()
        _, headers, _ = parse_response(self.request(port))
        self.assertTrue(headers["Date"].endswith(" GMT"))
        sent = email.utils.parsedate_to_datetime(headers["Date"]).timestamp()
        self.assertLess(abs(sent - time.time()), 5)

    def test_head_has_no_body(self):
        port = self.start()
        raw = self.request(port, CONNECT_TEST.replace(b"GET", b"HEAD", 1))
        status, _, body = parse_response(raw)
        self.assertEqual(status, "HTTP/1.1 200 OK")
        self.assertEqual(body, b"")

    def test_logs_one_line_per_request_when_enabled(self):
        port = self.start(log_requests=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.request(port)
        line = out.getvalue().strip()
        self.assertIn("127.0.0.1 'GET /api/v1/connect-test HTTP/1.1'", line)
        self.assertIn("Host='info.cspserver.net'", line)

    def test_healthcheck_is_not_logged(self):
        port = self.start(log_requests=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(responder.healthcheck(port), 0)
        self.assertEqual(out.getvalue(), "")

    def test_healthcheck_fails_when_nothing_listens(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]
        self.assertEqual(responder.healthcheck(free_port), 1)

    def test_silent_when_logging_disabled(self):
        port = self.start(log_requests=False)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.request(port)
        self.assertEqual(out.getvalue(), "")


class OptionsTest(unittest.TestCase):
    def test_reads_options_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"log_requests": False}, f)
        self.addCleanup(pathlib.Path(f.name).unlink)
        self.assertEqual(responder.load_options(f.name), {"log_requests": False})

    def test_missing_options_file_gives_defaults(self):
        self.assertEqual(responder.load_options("/nonexistent/options.json"), {})


if __name__ == "__main__":
    unittest.main()
