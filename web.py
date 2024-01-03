from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs

import inspect
import json
import os
import time


def send_404(req):
    req.send_response(404)
    req.end_headers()
    try:
        req.wfile.write(bytes("Not Found", "utf-8"))
    except:
        pass


def read_file(file):
    return open(file, "r").read()


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, routes, static_hosting, logging, *args, **kwargs):
        self.routes = routes
        self.static_hosting = static_hosting
        self.logging = logging
        super().__init__(*args, **kwargs)

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        status_code = 200
        headers = None
        content_type = None

        # handle static file hosting
        if isinstance(self.static_hosting, str):
            self.static_hosting = [self.static_hosting]
        if path.split("/")[1] in self.static_hosting:
            if os.path.isfile("." + path):
                contents = open("." + path, "rb").read()
                try:
                    contents = contents.decode("utf-8")
                except:
                    pass
                extention = path.split(".")[-1]
                match extention:
                    case "html":
                        content_type = "text/html"
                    case "css":
                        content_type = "text/css"
                    case "js":
                        content_type = "text/javascript"
                    case "ico":
                        content_type = "image/x-icon"
                self.send_response(200)
                self.send_header(
                    "Content-type", content_type or "application/octet-stream"
                )
                self.send_header("Cache-Control", "public, max-age=31536000")
                self.end_headers()
                try:
                    self.wfile.write(bytes(contents, "utf-8"))
                except:
                    self.wfile.write(contents)
                    pass
                return

        if path in self.routes:
            func = self.routes[path]
            sig = inspect.signature(func)

            if len(sig.parameters) == 0:
                response = func()
            else:
                cookie_str = self.headers.get("Cookie")
                cookie = SimpleCookie()
                cookie.load(cookie_str or "")
                cookies = {k: v.value for k, v in cookie.items()}
                query_params = parse_qs(url.query)
                # convert lists in values to strings
                query_params = {k: v[0] for k, v in query_params.items()}
                resp = type(
                    "Reponse",
                    (),
                    {"method": "GET", "params": query_params, "cookies": cookies},
                )
                response = func(resp)

            if response is None:
                return send_404(self)

            if isinstance(response, dict):
                if "status-code" in response:
                    status_code = response["status-code"]
                if "headers" in response:
                    headers = response["headers"]
                if "data" in response:
                    response = response["data"]
                else:
                    response = ""

            if isinstance(response, tuple):
                response, content_type = response

            self.send_response(status_code)

            if headers is not None:
                for header in headers:
                    self.send_header(header[0], header[1])
            else:
                self.send_header("Content-type", content_type or "text/html")

            self.end_headers()

            try:
                self.wfile.write(bytes(response, "utf-8"))
            except:
                pass
            return

        send_404(self)

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path
        status_code = 200
        headers = None
        content_type = None

        if path in self.routes:
            func = self.routes[path]
            sig = inspect.signature(func)

            if len(sig.parameters) == 0:
                response = func()
            else:
                content_length = int(self.headers["Content-Length"])
                post_data = self.rfile.read(content_length)

                try:
                    post_body = json.loads(post_data.decode("utf-8"))
                except:
                    post_body = parse_qs(post_data.decode("utf-8"))
                    # convert lists in values to strings
                    post_body = {k: v[0] for k, v in post_body.items()}

                cookie_str = self.headers.get("Cookie")
                cookie = SimpleCookie()
                cookie.load(cookie_str or "")
                cookies = {k: v.value for k, v in cookie.items()}
                resp = type(
                    "Reponse",
                    (),
                    {"method": "POST", "body": post_body, "cookies": cookies},
                )
                response = func(resp)

            if response is None:
                return send_404(self)

            if isinstance(response, dict):
                if "status-code" in response:
                    status_code = response["status-code"]
                if "headers" in response:
                    headers = response["headers"]
                if "data" in response:
                    response = response["data"]
                else:
                    response = ""

            if isinstance(response, tuple):
                response, content_type = response

            self.send_response(status_code)

            if headers is not None:
                for header in headers:
                    self.send_header(header[0], header[1])
            else:
                self.send_header("Content-type", content_type or "text/html")

            self.end_headers()

            try:
                self.wfile.write(bytes(response, "utf-8"))
            except:
                pass
            return

        send_404(self)

    def log_message(self, format, *args):
        if self.logging:
            GRAY = "\x1b[90m"
            PURPLE = "\x1b[95m"
            RESET = "\x1b[00m"
            remote = self.request.getpeername()
            remote = f"{remote[0]}:{remote[1]}"
            print(
                f"{GRAY}[{time.strftime('%d/%m/%Y %H:%M:%S')}]{PURPLE} ({remote}){RESET} {self.requestline}"
            )


class App:
    def __init__(self, routes, static_hosting=[], logging=False):
        self.routes = routes
        self.static_hosting = static_hosting
        self.logging = logging

    def run(self, host="0.0.0.0", port=3000):
        server_address = (host, port)
        httpd = HTTPServer(
            server_address,
            lambda *args, **kwargs: RequestHandler(
                self.routes, self.static_hosting, self.logging, *args, **kwargs
            ),
        )
        print(f"Starting server on port {port}...")
        httpd.serve_forever()


class Template:
    def __init__(self, file):
        self.file = file
        self.template = read_file(file)

    def render(self, context={}):
        out = self.template
        for key in context.keys():
            out = out.replace("{{" + key + "}}", context.get(key) or "")
        return out
