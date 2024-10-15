from common.model import ClientRequest
from common.utils import CalculateChecksum
from typing import Dict, List

import json
import os
import socket


class Client:
    def __init__(
        self,
        server_ip: str = "localhost",
        server_port: int = 8082,
        chunk_size: int = 256,
    ) -> None:
        self.__temporary_file_buffer = {}
        self.__base_path = "client_files/"
        self.__output_file = "client.txt"
        self.__server_address = (server_ip, server_port)
        self.__chunk_size = chunk_size
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.settimeout(180)

    def execute(self) -> None:
        while True:
            self.__temporary_file_buffer = {}

            file_name = str(input("File name: "))
            discarded_pkts = int(input("Discarded packets: "))
            transfer_object = ClientRequest(
                file_name=file_name, discarded_pkts=discarded_pkts
            )
            data_sent = json.dumps(transfer_object.__dict__)

            try:
                self.__sock.sendto(
                    data_sent.encode("iso-8859-1"), self.__server_address
                )
                data, _ = self.__sock.recvfrom(self.__chunk_size)
                data = data.decode("iso-8859-1")

                if "checksum" in data:
                    self.__clear_client_folder()
                    self.__receive_file()
                    self.__build_file()
                    self.__check_file_integrity(checksum=data)

                    # if not self.__check_file_integrity(checksum=data):
                    #     retransmission = str(
                    #         input("Do you want to retransmit the lost packets? [y/n] ")
                    #     ).lower()

                    #     if retransmission == "y":
                    #         self.__retransmit_lost_pkts()
                    #         self.__build_file()
                    #         self.__check_file_integrity(checksum=data)

                else:
                    print(data)

            except socket.error as e:
                print(f"Socket error: {str(e)}")

            except Exception as e:
                print(f"Other exception: {str(e)}")

            continue_request = str(input("Continue request? [y/n] ")).lower()
            if continue_request == "n":
                self.__sock.sendto(
                    "Finish connection".encode("iso-8859-1"), self.__server_address
                )
                break

        self.__sock.close()

    def __build_file(self) -> None:
        with open(self.__base_path + self.__output_file, "wb") as file:
            for chunk in self.__temporary_file_buffer.values():
                file.write(chunk)

    def __receive_file(self) -> None:
        continue_receiving = True

        while continue_receiving:
            pkt_number, _ = self.__sock.recvfrom(self.__chunk_size)
            pkt_number = pkt_number.decode("iso-8859-1")

            chunk, _ = self.__sock.recvfrom(self.__chunk_size)

            if chunk == b"EOF":
                print("File transfer complete.")
                continue_receiving = False
            else:
                self.__temporary_file_buffer.update({pkt_number: chunk})

    def __check_file_integrity(self, checksum: int) -> bool:
        checksum = json.loads(checksum).get("checksum")

        if CalculateChecksum.execute(self.__base_path + self.__output_file) != checksum:
            print("File transfer fail: different checksum")
            return False

        print("File transfer complete: correct checksum")
        return True

    def __clear_client_folder(self) -> None:
        if os.path.isfile(self.__base_path + self.__output_file):
            os.remove(self.__base_path + self.__output_file)

    def __retransmit_lost_pkts(self) -> None:
        self.__sock.sendto("Retransmit".encode("iso-8859-1"), self.__server_address)

        continue_retransmission = True
        while continue_retransmission:
            data, _ = self.__sock.recvfrom(self.__chunk_size)
            answer = data.decode("iso-8859-1")

            if answer == "Finished":
                continue_retransmission = False

            if answer == "Send":
                if not self.__temporary_file_buffer.get(answer):
                    self.__sock.sendto(answer, self.__server_address)
                    lost_pkt_chunk, _ = self.__sock.recvfrom(self.__chunk_size)
                    self.__temporary_file_buffer.update({answer: lost_pkt_chunk})
                else:
                    self.__sock.sendto("Ok".encode("iso-8859-1"), self.__server_address)


if __name__ == "__main__":
    client = Client()
    client.execute()
