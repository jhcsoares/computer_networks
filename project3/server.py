from models.http_request import HTTPRequest
from typing import Dict, Tuple

import os
import socket
import threading


class Server:
    def __init__(self, ip: str = "localhost", port: int = 8082) -> None:
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__sock.bind((ip, port))

        # Maximum number of connections
        self.__sock.listen(5)

        self.__server_files_root_dir = "server_files/"

    ########################################## File Handlers ##########################################

    def __get_file_content_type(self, file_extension: str) -> str:
        if file_extension == "html":
            content_type = "text/html"

        if file_extension == "jpg" or file_extension == "jpeg":
            content_type = "image/jpeg"

        return content_type

    def __get_server_file(self, file_path: str) -> bytes:
        with open(file=self.__server_files_root_dir + file_path, mode="rb") as f:
            file_content = f.read()

        return file_content

    def __file_request_handler(self, file: str) -> Tuple[str, str]:
        file_extension = file.split(".")[1]

        content_type = self.__get_file_content_type(file_extension=file_extension)

        file = self.__get_server_file(file_path=file)

        response = (
            "HTTP/1.1 200 OK\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(file)}\r\n"
            "\r\n"
        )

        return response, file

    def __file_doesnt_exist_handler(self) -> str:
        file = self.__get_html_file("/file_not_found.html")

        response = (
            "HTTP/1.1 404 File not found\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(file)}\r\n"
            "\r\n"
            f"{file}"
        )

        return response

    def __check_file_existency(self, file_path: str) -> bool:
        if os.path.exists(self.__server_files_root_dir + file_path):
            return True

        return False

    def __get_html_file(self, file_path: str) -> str:
        if "/" in file_path:
            file_path = file_path[1:]

        with open(file=file_path, mode="r") as f:
            html_content = f.read()

        return html_content

    ######################################################################################################

    ########################################## Request Handlers ##########################################

    def __get_query_strings(self, url: str) -> Dict[str, str]:
        result = {}

        query_strings = url.split("?")[1:]

        for query_string in query_strings:
            key, value = query_string.split("=")
            result[key] = value

        return result

    def __get_endpoint(self, url: str) -> str:
        return url.split("?")[0]

    def __parse_http_request(self, http_request: str) -> HTTPRequest:
        http_request_dict = {}

        # Check if request is not empty
        if http_request:
            # Separate each line of the HTTP request
            http_lines = http_request.strip().split("\n")

            # Handle request line
            http_request_line = http_lines[0]
            http_request_line_words = http_request_line.strip().split(" ")
            http_request_dict.update(
                {
                    "method": http_request_line_words[0],
                    "endpoint": self.__get_endpoint(http_request_line_words[1]),
                    "query_strings": self.__get_query_strings(
                        http_request_line_words[1]
                    ),
                    "http_version": http_request_line_words[2],
                }
            )

            # Handle header lines
            http_request_headers_lines = http_lines[1:]
            for http_request_header_line in http_request_headers_lines:
                header, value = http_request_header_line.strip().split(": ")
                header = header.lower().replace("-", "_")
                http_request_dict[header] = value

        return HTTPRequest(**http_request_dict)

    def __handle_client(self, client_socket: socket.socket) -> None:
        http_request = client_socket.recv(1024).decode("utf-8")

        parsed_request = self.__parse_http_request(http_request=http_request)

        if parsed_request.endpoint == "/home.html":
            self.__home_endpoint(client_socket=client_socket)

        if parsed_request.endpoint == "/get_file":
            self.__get_file_endpoint(
                client_socket=client_socket, request=parsed_request
            )

        client_socket.close()

    ##############################################################################################

    ########################################## Endpoints ##########################################

    def __home_endpoint(self, client_socket: socket.socket) -> None:
        html_content = self.__get_html_file(file_path="/home.html")

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(html_content)}\r\n"
            "\r\n"
            f"{html_content}"
        )

        client_socket.sendall(response.encode("utf-8"))

    def __get_file_endpoint(
        self, client_socket: socket.socket, request: HTTPRequest
    ) -> None:
        requested_file = request.query_strings.get("file")

        if self.__check_file_existency(file_path=requested_file):
            response, file = self.__file_request_handler(file=requested_file)
            client_socket.sendall(response.encode("utf-8"))
            client_socket.sendall(file)

        else:
            response = self.__file_doesnt_exist_handler()
            client_socket.sendall(response.encode("utf-8"))

    ###################################################################################################

    def execute(self) -> None:
        while True:
            client_socket, _ = self.__sock.accept()

            client_thread = threading.Thread(
                target=self.__handle_client, args=(client_socket,)
            )

            client_thread.start()

    ###################################################################################################


if __name__ == "__main__":
    server = Server()
    server.execute()
