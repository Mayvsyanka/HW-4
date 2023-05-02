from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import urllib.parse
import socket
import mimetypes
import pathlib
from jinja2 import Environment, FileSystemLoader
import json
from datetime import datetime

BASE_DIR = pathlib.Path()
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000
env = Environment(loader=FileSystemLoader('templates'))


def send_data(body):
    socket_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_send.sendto(body, (SERVER_IP, SERVER_PORT))
    socket_send.close()


class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == '/':
            self.send_html_file('index.html')

        elif pr_url.path == '/message':
            self.send_html_file('message.html')

        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static(self.path)
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data(body)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_static(self, filename):
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-type", mime_type)
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def send_html_file(self, filename, st=200):
        self.send_response(st)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def render_template(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open('blog.json') as fd:
            r = json.load(fd)
        template = env.get_template(filename)
        html = template.render(blogs=r)
        self.wfile.write(html.encode)


def run(server=HTTPServer, handler=HttpHandler):
    address = ("", 3000)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def save_data(raw_data):
    body = urllib.parse.unquote_plus(raw_data.decode())
    data_dict = {key: value for key, value in [
        el.split('=') for el in body.split('&')]}
    with open("storage/data.json", 'r') as fh:
        file_content = fh.read().strip()
        if not file_content:
            info = {}
        else:
            with open("storage/data.json", 'r') as fh:
                info = json.load(fh)
        info.update({str(datetime.now()): data_dict})
    with open("storage/data.json", 'w') as wfh:
        json.dump(info, wfh)


def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            data, address = server_socket.recvfrom(1024)
            save_data(data)
    except KeyboardInterrupt:
        print("Socket server stopped")
    finally:
        server_socket.close()


if __name__ == '__main__':
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(SERVER_IP, SERVER_PORT))
    thread_socket.start()
