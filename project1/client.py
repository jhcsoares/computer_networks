from common.model import ClientRequest
from common.utils import CalculateChecksum

import json
import os
import shutil
import socket


class Client:
    def __init__(
        self,
        server_ip: str = "localhost",
        server_port: int = 8082,
        chunk_size: int = 256,
    ) -> None:

        self.__client_address = ""
        self.__checksum = ""
        self.__temporary_file_buffer = {}
        self.__base_path = "client_files/"
        self.__output_file = ""
        self.__server_address = (server_ip, server_port)
        self.__chunk_size = chunk_size
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.settimeout(10000)

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

                if "client_address" in data:
                    self.__client_address = str(json.loads(data).get("client_address"))

                    data, _ = self.__sock.recvfrom(self.__chunk_size)
                    data = data.decode("iso-8859-1")

                    if "checksum" in data:
                        self.__output_file = file_name
                        self.__checksum = json.loads(data).get("checksum")
                        self.__receive_file()
                        self.__build_file()

                        if not self.__check_file_integrity(checksum=self.__checksum):
                            retransmission = str(
                                input(
                                    "Do you want to retransmit the lost packets? [y/n] "
                                )
                            ).lower()

                            if retransmission == "y":
                                self.__retransmit_lost_pkts()
                                self.__receive_lost_pkts()
                                self.__clear_client_folder()
                                self.__build_file()
                                self.__check_file_integrity(checksum=self.__checksum)

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

        self.__clear_client_folder()
        self.__sock.close()

    def __build_file(self) -> None:
        os.makedirs(self.__base_path + self.__client_address + "/", exist_ok=True)

        with open(
            self.__base_path + self.__client_address + "/" + self.__output_file, "wb"
        ) as file:
            for pkt_number in sorted(self.__temporary_file_buffer.keys(), key=int):
                chunk = self.__temporary_file_buffer[pkt_number]
                if chunk != b"EOF":
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

            self.__temporary_file_buffer.update({pkt_number: chunk})

    def __check_file_integrity(self, checksum: str) -> bool:
        if (
            CalculateChecksum.execute(
                self.__base_path + self.__client_address + "/" + self.__output_file
            )
            != checksum
        ):
            print("File transfer fail: different checksum")
            return False

        print("File transfer complete: correct checksum")
        return True

    def __clear_client_folder(self) -> None:
        shutil.rmtree(self.__base_path + self.__client_address + "/")

    def __retransmit_lost_pkts(self) -> None:
        for pkt_number in self.__temporary_file_buffer.keys():
            self.__sock.sendto(
                json.dumps({"Retransmit": pkt_number}).encode("iso-8859-1"),
                self.__server_address,
            )

        self.__sock.sendto(
            "Finished retransmission".encode("iso-8859-1"),
            self.__server_address,
        )

    def __receive_lost_pkts(self):
        continue_receiving = True

        while continue_receiving:
            pkt_number_rcv, _ = self.__sock.recvfrom(self.__chunk_size)
            pkt_number_rcv = pkt_number_rcv.decode("utf-8")
            chunk, _ = self.__sock.recvfrom(self.__chunk_size)

            if pkt_number_rcv == "Finished":
                continue_receiving = False

            else:
                self.__temporary_file_buffer.update({pkt_number_rcv: chunk})


if __name__ == "__main__":
    client = Client()
    client.execute()
