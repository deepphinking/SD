"""
Cliente TCP - Conversor de Moedas (menu conduzido pelo servidor)
Sistemas Distribuidos

O cliente faz connect() (handshake) e, na MESMA conexao, troca as 3 mensagens
do protocolo com o servidor:
  1) "MENU"                 -> recebe e mostra a lista numerada
  2) "ESCOLHA;<n>"          -> recebe a pergunta pedindo o valor em R$
  3) "CONVERTE;<n>;<valor>" -> recebe o resultado da conversao
"""

import socket

HOST = "192.168.86.33" #IP do Servidor
PORT = 6666


def pedir(sock, msg):
    """Envia uma mensagem ao servidor e devolve a resposta (texto)."""
    sock.sendall(msg.encode("utf-8"))
    dados = sock.recv(4096)
    return dados.decode("utf-8")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))  # handshake
    except ConnectionRefusedError:
        print("ERRO: nao foi possivel conectar. O servidor TCP esta ligado?")
        return

    print("=== Conversor de Moedas (TCP) ===")
    print("Digite 'sair' a qualquer momento para encerrar.\n")

    try:
        menu = pedir(sock, "MENU")
        while True:
            print(menu)
            escolha = input("\nDigite o numero da moeda desejada: ").strip()
            if escolha.lower() == "sair":
                break

            pergunta = pedir(sock, f"ESCOLHA;{escolha}")
            if pergunta.startswith("ERRO"):
                print(">> " + pergunta + "\n")
                continue
            print("\n" + pergunta)

            valor = input("> ").strip()
            if valor.lower() == "sair":
                break

            resultado = pedir(sock, f"CONVERTE;{escolha};{valor}")
            print(">> " + resultado + "\n")
    except (ConnectionResetError, BrokenPipeError):
        print(">> ERRO: conexao encerrada pelo servidor.")
    except KeyboardInterrupt:
        print()
    finally:
        sock.close()
        print("Cliente encerrado.")


if __name__ == "__main__":
    main()
