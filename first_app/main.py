import pathlib
import urllib.parse
import mimetypes
import json
import socket
import logging
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

BASE_DIR = pathlib.Path()
SERVER_IP = "127.0.0.1"
DOCKER_IP = "0.0.0.0"
SERVER_PORT = 5000
APP_PORT = 3000
MESSAGE_LEN = 1024
ERR_STATUS = 404
NORM_STATUS = 200
RESPONSE_VAL = 302


def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT))
    client_socket.close()


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(body)
        self.send_response(RESPONSE_VAL)
        self.send_header('Location', '/message.html')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html('index.html')
            case "/message.html":
                self.send_html('message.html')
            case _:
                path = BASE_DIR / route.path[1:]
                if path.exists():
                    self.send_static(path)
                else:
                    self.send_html('error.html', ERR_STATUS)

    def send_html(self, filename, status_code=NORM_STATUS):
        self.send_response(status_code)
        self.send_header('Content - Type', 'text / html')
        self.end_headers()

        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(NORM_STATUS)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content - Type', mime_type)
        else:
            self.send_header('Content - Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=HTTPHandler):
    address = (DOCKER_IP, APP_PORT)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def run_socker_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            data, address = server_socket.recvfrom(MESSAGE_LEN)
            save_data(data)
    except KeyboardInterrupt:
        logging.info("Socket server stopped")
    finally:
        server_socket.close()


def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())
    try:
        payload = {key: value for key, value in [el.split('=') for el in body.split('&')]}
    except ValueError as e:
        logging.error(f"Field parse data: {body} with {e}")
        payload = None
    try:
        with open(BASE_DIR.joinpath('storage/data.json'), 'r', encoding='utf-8') as file:
            read_write_data = json.load(file)
    except ValueError:
        read_write_data = {}
    if payload:
        read_write_data[str(datetime.datetime.now())] = payload
    try:
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as file:
            json.dump(read_write_data, file, ensure_ascii=False, indent=2)
    except OSError as e:
        logging.error(f"Field write data: {body} with {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(threadName)s %(message)s")
    STORAGE_DIR = pathlib.Path().joinpath('storage')
    print(STORAGE_DIR)
    FILE_STORAGE = STORAGE_DIR / 'data.json'
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, 'w', encoding='utf-8') as fl:
            json.dump({}, fl, ensure_ascii=False, indent=2)

    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socker_server, args=(SERVER_IP, SERVER_PORT))
    thread_socket.start()
