import socket
import protocol

from threading import Thread, Event
from logging_config import logger


stop_chat_talk_event = Event()

def chat_talk(sock: socket.socket, is_p2p=False) -> None:
    logger.info(f'{chat_talk.__name__} has started {"in P2P mode" if is_p2p else ""}')
    init = True

    while not stop_chat_talk_event.is_set():
        try:
            msg = input().strip()
        except EOFError:
            break

        if msg == "/exit":
            break

        if not msg == "/p2p" and not stop_chat_talk_event.is_set():
            try:
                protocol.send_segment(sock, msg)
            except OSError:
                logger.warning("Switch to P2P, error in sending this first msg")
                init = False
                break
            continue
        if not is_p2p:
            break
        else:
            print("You have already in P2P conversation")

    if not is_p2p and not stop_chat_talk_event.is_set() and init:
        listen_for_p2p_conn(sock)
    sock.close()

    logger.info(f'{chat_talk.__name__} has closed {"in P2P mode" if is_p2p else ""}')


def chat_listen(sock: socket.socket, is_p2p=False) -> None:
    logger.info(f'{chat_listen.__name__} has started {"in P2P mode" if is_p2p else ""}')

    while True:
        valid_msg, msg = protocol.get_payload(sock)

        if not valid_msg:
            print(f"Error in accepting the message: {msg}")
            if ConnectionAbortedError.__name__ in msg or ConnectionResetError.__name__ in msg:
                break
            continue

        if "/exit" in msg:
            break

        if is_p2p or not "P2P_REQUEST" in msg:
            print(msg)
            if "Waiting for the other side to approve a P2P conversation" in msg:
                is_p2p = True
                break
            continue
        break

    if not is_p2p:
        protocol.send_segment(sock, "P2P_ACK")
        stop_chat_talk_event.set()
        peer_addr = msg.split(':')[-1]
        open_p2p_conn(peer_addr.split(',')[0].strip("'"), int(peer_addr.split(',')[1]))
    sock.close()

    logger.info(f'{chat_listen.__name__} has closed {"in P2P mode" if is_p2p else ""}')


def listen_for_p2p_conn(STUN_sock: socket.socket) -> None:
    peer_listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_listen_sock.bind((protocol.LISTEN_ANY_IP, 0))
    peer_listen_sock.listen(1)
    logger.info(f"Waiting for a peer to connect: Listening on {protocol.LISTEN_ANY_IP}:{peer_listen_sock.getsockname()[1]}")

    protocol.send_segment(STUN_sock, f"P2P_REQUEST:{STUN_sock.getsockname()[0]},{peer_listen_sock.getsockname()[1]}")
    peer_conn_sock, peer_addr = peer_listen_sock.accept()
    logger.info(f"{peer_addr} has connected - the conversation from now on is P2P")

    start_chat_threads(peer_conn_sock, True)


def open_p2p_conn(peer_conn_ip: str, peer_conn_port: int) -> None:
    peer_conn_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_conn_sock.connect((peer_conn_ip, peer_conn_port))
    logger.info(f"You have connected to a pear - the conversation from now on is P2P")

    stop_chat_talk_event.clear()
    start_chat_threads(peer_conn_sock, True)


def start_chat_threads(conn_sock: socket.socket, is_p2p=False) -> None:
    talk_thread = Thread(target=chat_talk, args=(conn_sock, is_p2p))
    listen_thread = Thread(target=chat_listen, args=(conn_sock, is_p2p))
    talk_thread.start()
    listen_thread.start()


def main():
    server_ip = input("Server IP: ").strip()  # for LAN usages dont put the server as loopback (goes to P2P connection)
    server_port = int(input("Server Port: ").strip())

    conn_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_sock.connect((server_ip, server_port))

    start_chat_threads(conn_sock)


if __name__ == "__main__":
    main()

