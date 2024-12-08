from models.file_data import FileData
from models.response import Response
from utils.calculate_checksum import CalculateChecksum

import keyboard
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

    def __check_file_existency(self, file_path: str) -> bool:
        if os.path.exists(self.__server_files_root_dir + file_path):
            return True

        return False

    def __send_file(self, file_path: str, client_socket: socket.socket) -> None:
        with open(file=self.__server_files_root_dir + file_path, mode="rb") as f:
            while chunk := f.read(1024):
                client_socket.sendall(chunk)

    def __client_file_request(
        self, file_path: str, client_socket: socket.socket
    ) -> None:
        if self.__check_file_existency(file_path=file_path):
            file_checksum = CalculateChecksum.execute(
                file_path=self.__server_files_root_dir + file_path
            )

            file_size = os.path.getsize(
                filename=self.__server_files_root_dir + file_path
            )

            client_socket.sendall(
                Response(
                    status=200,
                    message=FileData(
                        checksum=file_checksum, size=file_size
                    ).serialize(),
                ).encode()
            )

            self.__send_file(file_path=file_path, client_socket=client_socket)

        else:
            client_socket.sendall(
                Response(status=403, message="File not found").encode()
            )

    def __client_chat(self, client_socket: socket.socket) -> None:
        while True:
            event = keyboard.read_event()

            if event.name == "esc":
                client_socket.sendall("esc".encode("utf-8"))
                break

            if event.event_type == "down":
                key = self.__key_handler(event.name)

                if key:
                    print(key, end="", flush=True)

                    client_socket.sendall(key.encode("utf-8"))

    def __key_handler(self, key: str) -> str:
        control_keys = [
            "right shift",
            "left shift",
            "right ctrl",
            "left ctrl",
            "backspace",
            "delete",
            "alt gr",
            "esc",
            "alt",
            "tab",
            "up",
            "right",
            "down",
            "left",
            "backspace",
        ]

        if key == "space":
            return " "

        elif key == "enter":
            return "\n"

        elif key in control_keys:
            return ""

        else:
            return key

    def __handle_client(self, client_socket: socket.socket) -> None:
        while True:
            message = client_socket.recv(1024).decode("utf-8")

            if message.lower() == "exit":
                break

            if message.lower() == "chat":
                self.__client_chat(client_socket=client_socket)

            else:
                self.__client_file_request(
                    file_path=message, client_socket=client_socket
                )

        client_socket.close()

    def execute(self) -> None:
        while True:
            client_socket, client_address = self.__sock.accept()

            client_thread = threading.Thread(
                target=self.__handle_client, args=(client_socket,)
            )

            client_thread.start()


if __name__ == "__main__":
    server = Server()
    server.execute()
