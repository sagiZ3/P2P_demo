import socket
import protocol

from threading import Thread
from logging_config import logger
from time import sleep

first_conn_sock: socket.socket
first_addr: tuple[str, int]
second_conn_sock: socket.socket
second_addr: tuple[str, int]

def handle_client(sock: socket.socket) -> None:
    other_sock = first_conn_sock
    if sock == first_conn_sock:
        other_sock = second_conn_sock

    while True:
        valid_msg, client_msg = protocol.get_payload(sock)

        if not valid_msg:
            protocol.send_segment(sock, f"Error in sending the message: {client_msg}")
            continue

        if "P2P_ACK" in client_msg:
            break

        if "P2P_REQUEST" in client_msg:
            # protocol.send_segment(sock, "Waiting for the other side to approve a P2P conversation")
            protocol.send_segment(other_sock, "The other side want to open a P2P conversation\n"
                                              f"{client_msg}")
            break
        broadcast(client_msg)

    sleep(1)
    sock.close()


def broadcast(msg: str) -> None:
    protocol.send_segment(first_conn_sock, msg)
    protocol.send_segment(second_conn_sock, msg)


def main():
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((protocol.LISTEN_ANY_IP, protocol.CONNECTION_PORT))
    listen_sock.listen(2)

    logger.info(f"SERVER: Listening on {protocol.LISTEN_ANY_IP}:{protocol.CONNECTION_PORT}")

    global first_conn_sock
    global first_addr
    global second_conn_sock
    global second_addr

    first_conn_sock, first_addr = listen_sock.accept()
    logger.info(f"{first_addr} has connected to the server")
    second_conn_sock, second_addr = listen_sock.accept()
    logger.info(f"{second_addr} has connected to the server")

    first_thread = Thread(target=handle_client, args=(first_conn_sock,))
    second_thread = Thread(target=handle_client, args=(second_conn_sock,))

    first_thread.start()
    second_thread.start()

if __name__ == "__main__":
    main()
