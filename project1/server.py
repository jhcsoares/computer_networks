from common.model import ClientRequest
from common.utils import CalculateChecksum
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple

import copy
import json
import os
import random
import socket


class Server:
    def __init__(
        self, host: str = "localhost", port: int = 8082, chunk_size: int = 256
    ) -> None:
        self.__base_path = "server_files/"
        self.__chunk_size = chunk_size
        self.__temporary_file_buffer = {}
        self.__client_retransmit_pkts_dict = {}
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__sock.bind((host, port))
        self.executor = ThreadPoolExecutor(max_workers=10)

    def execute(self) -> None:
        while True:
            data, client_address = self.__sock.recvfrom(self.__chunk_size)
            self.executor.submit(self.__handle_client, data, client_address)

    def __handle_client(self, data: bytes, client_address: Tuple[str, int]) -> None:
        keep_connection = True
        while keep_connection:
            data = data.decode("iso-8859-1")

            print(f"Client {client_address} request: {data}")

            if "Retransmit" in data:
                pkt_number = json.loads(data)["Retransmit"]
                self.__client_retransmit_pkts_dict.update(
                    {client_address: {pkt_number: "OK"}}
                )

            elif "Finished retransmission" == data:
                self.__retransmit_lost_pkts(client_address=client_address)
                del self.__client_retransmit_pkts_dict[client_address]

            elif data == "Finish connection":
                keep_connection = False

            else:
                data = json.loads(data)
                transfer_object = ClientRequest(**data)

                if self.__check_file_existency(transfer_object.file_name):

                    self.__sock.sendto(
                        json.dumps({"client_address": client_address[1]}).encode(
                            "iso-8859-1"
                        ),
                        client_address,
                    )

                    chunks_dict = self.__get_file_chunks(
                        file_path=transfer_object.file_name
                    )

                    self.__temporary_file_buffer.update(
                        {client_address: copy.deepcopy(chunks_dict)}
                    )

                    self.__remove_chunks(
                        chunks_dict=chunks_dict,
                        discarded_pkts=transfer_object.discarded_pkts,
                    )

                    checksum = CalculateChecksum.execute(
                        self.__base_path + transfer_object.file_name
                    )

                    self.__transfer_data(
                        chunks_dict=chunks_dict,
                        checksum=checksum,
                        client_address=client_address,
                    )

                else:
                    self.__sock.sendto(
                        "File does not exist".encode("iso-8859-1"), client_address
                    )

    def __check_file_existency(self, file_path: str) -> bool:
        if os.path.exists(self.__base_path + file_path):
            return True
        return False

    def __get_file_chunks(self, file_path: str) -> Dict[str, bytes]:
        chunks_dict = {}
        i = 0
        with open(self.__base_path + file_path, "rb") as file:
            continue_reading = True
            while continue_reading:
                chunk = file.read(self.__chunk_size)
                if not chunk:
                    continue_reading = False

                else:
                    chunks_dict.update({str(i): chunk})
                    i += 1

        chunks_dict.update({str(i): b"EOF"})

        return chunks_dict

    def __remove_chunks(self, chunks_dict: Dict[str, bytes], discarded_pkts: int):
        if discarded_pkts >= len(chunks_dict):
            chunks_dict.clear()

        else:
            for _ in range(discarded_pkts - 1):
                key = random.choice(list(chunks_dict.keys()))
                del chunks_dict[key]

    def __transfer_data(
        self,
        chunks_dict: Dict[str, bytes],
        checksum: str,
        client_address: Tuple[str, int],
    ) -> None:

        checksum_dict = json.dumps({"checksum": checksum})
        self.__sock.sendto(checksum_dict.encode("iso-8859-1"), client_address)

        for register in chunks_dict.items():
            pkt_number = register[0]
            chunk = register[1]

            self.__sock.sendto(pkt_number.encode("iso-8859-1"), client_address)
            self.__sock.sendto(chunk, client_address)

    def __retransmit_lost_pkts(self, client_address: Tuple[str, int]) -> None:
        lost_pkts_list = self.__check_missing_pkts(client_address=client_address)

        for lost_pkt in lost_pkts_list:
            chunk = self.__temporary_file_buffer.get(client_address).get(lost_pkt)
            self.__sock.sendto(lost_pkt.encode("utf-8"), client_address)
            self.__sock.sendto(chunk, client_address)

        self.__sock.sendto("Finished".encode("iso-8859-1"), client_address)
        self.__sock.sendto("EOF".encode("iso-8859-1"), client_address)

    def __check_missing_pkts(self, client_address: Tuple[str, int]) -> List[str]:
        lost_pkts_list = []

        for pkt_number in self.__temporary_file_buffer.get(client_address).keys():
            if not (
                self.__client_retransmit_pkts_dict.get(client_address).get(pkt_number)
            ):
                lost_pkts_list.append(pkt_number)

        return lost_pkts_list


if __name__ == "__main__":
    server = Server()
    server.execute()
