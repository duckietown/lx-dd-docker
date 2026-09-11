"""Run a small HTTP server for the Docker learning exercise."""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Listen on every network interface inside the container. Docker's --publish
# rule still controls which base-station address can reach this server.
HOST = "0.0.0.0"
# This is the port inside the container, not automatically a host port.
PORT = 8080
# Store bytes so Content-Length matches exactly what the handler sends.
RESPONSE_BODY = b"Hello from the Duckietown Docker LX.\n"


class HelloHandler(BaseHTTPRequestHandler):
    """Reply to the one endpoint used by the exercise."""

    def do_GET(self) -> None:
        """Return a short response for the root path."""
        # Keep the example focused on one predictable endpoint: /.
        if self.path != "/":
            self.send_error(
                HTTPStatus.NOT_FOUND, "Only the root path is available."
            )
            return

        # An HTTP response sends its status line, headers, then body in order.
        self.send_response(HTTPStatus.OK)
        # Tell the client that the response is UTF-8 text and how many bytes follow.
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(RESPONSE_BODY)))
        # Finish the headers before writing the body bytes to the client.
        self.end_headers()
        self.wfile.write(RESPONSE_BODY)


def main() -> None:
    """Start the server until Docker stops the container."""
    # Bind inside the container so Docker can forward the published port to it.
    server = ThreadingHTTPServer((HOST, PORT), HelloHandler)
    print(f"Serving http://{HOST}:{PORT}", flush=True)

    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
