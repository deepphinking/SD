"""
Cliente UDP - Conversor de Moedas (menu conduzido pelo servidor)
Sistemas Distribuidos

O cliente e simples: pede o menu ao servidor, mostra o que o servidor envia,
e repassa o que o usuario digita. Toda a logica (lista, validacao, cotacao)
esta no servidor.

Fluxo:
  1) pede "MENU" e exibe a lista numerada
  2) le o numero da moeda e envia "ESCOLHA;<n>" (servidor responde a pergunta)
  3) le o valor em R$ e envia "CONVERTE;<n>;<valor>" (servidor responde o resultado)
"""

import socket

HOST = "192.168.86.33" # #IP do Servidor
PORT = 8888


def pedir(sock, msg):
    """Envia uma mensagem ao servidor e devolve a resposta (texto)."""
    sock.sendto(msg.encode("utf-8"), (HOST, PORT))
    dados, _ = sock.recvfrom(4096)
    return dados.decode("utf-8")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(20.0)  # a consulta a PTAX pode demorar alguns segundos

    print("=== Conversor de Moedas (UDP) ===")
    print("Digite 'sair' a qualquer momento para encerrar.\n")

    try:
        menu = pedir(sock, "MENU")
        while True:
            print(menu)
            escolha = input("\nDigite o numero da moeda desejada: ").strip()
            if escolha.lower() == "sair":
                break

            # 2) envia a escolha; servidor valida e pergunta o valor
            pergunta = pedir(sock, f"ESCOLHA;{escolha}")
            if pergunta.startswith("ERRO"):
                print(">> " + pergunta + "\n")
                continue
            print("\n" + pergunta)  # a "pergunta do servidor" pelo valor

            valor = input("> ").strip()
            if valor.lower() == "sair":
                break

            # 3) envia numero + valor; servidor devolve a conversao
            resultado = pedir(sock, f"CONVERTE;{escolha};{valor}")
            print(">> " + resultado + "\n")
    except socket.timeout:
        print(">> ERRO: sem resposta do servidor (ele esta ligado? tem internet?).")
    except KeyboardInterrupt:
        print()
    finally:
        sock.close()
        print("Cliente encerrado.")


if __name__ == "__main__":
    main()
