from models.file_data import FileData
from models.response import Response
from utils.calculate_checksum import CalculateChecksum

import json
import os
import socket
import shutil


class Client:
    def __init__(self, server_ip: str = "localhost", server_port: int = 8082) -> None:
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((server_ip, server_port))

        self.__client_files_root_dir = "client_files/"
        self.__client_ip = self.__sock.getsockname()[0]
        self.__client_port = str(self.__sock.getsockname()[1])

        self.__client_folder_path = (
            self.__client_files_root_dir
            + self.__client_ip
            + "/"
            + self.__client_port
            + "/"
        )

    def __client_file_request(self, file_path: str) -> None:
        server_response = Response(**json.loads(self.__sock.recv(1024).decode("utf-8")))

        if server_response.status == 403:
            print(server_response.message)

        elif server_response.status == 200:
            file_data = FileData(**json.loads(server_response.message))

            file_checksum = file_data.checksum
            file_size = file_data.size

            self.__save_file(file_path=file_path, file_size=file_size)

            received_file_checksum = CalculateChecksum.execute(
                file_path=self.__client_folder_path + file_path
            )

            if file_checksum == received_file_checksum:
                print("File transmission successfully finished")

            else:
                print("File transmission completed unsuccessfully")

    def __create_client_folder(self, folder_path: str) -> None:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def __remove_client_folder(self) -> None:
        if os.path.exists(self.__client_folder_path):
            shutil.rmtree(self.__client_folder_path)

    def __save_file(self, file_path: str, file_size: int) -> None:
        self.__create_client_folder(folder_path=self.__client_folder_path)

        received_chunks = 0

        with open(file=self.__client_folder_path + file_path, mode="wb") as f:
            while received_chunks < file_size:
                chunk = self.__sock.recv(1024)
                f.write(chunk)

                received_chunks += len(chunk)

    def __client_chat(self) -> None:
        while True:
            key = self.__sock.recv(1024).decode("utf-8")

            if key == "esc":
                print()
                break

            print(self.__key_handler(key=key), end="", flush=True)

    def __key_handler(self, key: str) -> str:
        if key == "space":
            return " "

        elif key == "enter":
            return "\n"

        else:
            return key

    def execute(self) -> None:
        while True:

            client_message = input("Request: ")

            self.__sock.sendall(client_message.encode("utf-8"))

            if client_message.lower() == "exit":
                break

            if client_message.lower() == "chat":
                self.__client_chat()

            else:
                self.__client_file_request(file_path=client_message)

        self.__remove_client_folder()

        self.__sock.close()


if __name__ == "__main__":
    client = Client()
    client.execute()
