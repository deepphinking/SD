"""
Servidor TCP - Conversor de Moedas (menu + cotacao REAL via API PTAX do BCB)
Sistemas Distribuidos

O SERVIDOR conduz o dialogo por um protocolo simples de 3 mensagens:
  1) cliente envia "MENU"                  -> lista numerada
  2) cliente envia "ESCOLHA;<n>"           -> pergunta pedindo o valor em R$
  3) cliente envia "CONVERTE;<n>;<valor>"  -> resultado da conversao

TCP e ORIENTADO A CONEXAO (SOCK_STREAM): listen() -> accept() -> recv()/send()
-> close(), com handshake de 3 vias antes da troca de dados. As tres mensagens
trafegam na MESMA conexao.

Obs.: consulta olinda.bcb.gov.br via HTTPS; precisa de internet na maquina.
"""

import socket
import json
import urllib.request
import urllib.parse
from datetime import date, timedelta

HOST = "192.168.86.33" #IP do Servidor
PORT = 6666

MOEDAS = [
    ("USD", "Dolar americano"),
    ("EUR", "Euro"),
    ("GBP", "Libra esterlina"),
    ("JPY", "Iene japones"),
    ("CHF", "Franco suico"),
    ("CAD", "Dolar canadense"),
    ("AUD", "Dolar australiano"),
]

BASE = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        "CotacaoMoedaAberturaOuIntermediario(codigoMoeda=@codigoMoeda,"
        "dataCotacao=@dataCotacao)")


def _montar_url(codigo, data_mmddyyyy):
    params = {
        "@codigoMoeda": f"'{codigo}'",
        "@dataCotacao": f"'{data_mmddyyyy}'",
        "$format": "json",
        "$select": "cotacaoCompra,dataHoraCotacao",
    }
    return BASE + "?" + urllib.parse.urlencode(params, safe="'")


def consultar_ptax(codigo):
    hoje = date.today()
    for i in range(0, 10):
        d = hoje - timedelta(days=i)
        url = _montar_url(codigo, d.strftime("%m-%d-%Y"))
        with urllib.request.urlopen(url, timeout=15) as resp:
            dados = json.load(resp)
        valores = dados.get("value", [])
        if valores:
            item = valores[0]
            return float(item["cotacaoCompra"]), item["dataHoraCotacao"]
    raise RuntimeError("nenhuma cotacao encontrada nos ultimos 10 dias")


def gerar_menu():
    linhas = ["Moedas disponiveis:"]
    for i, (cod, nome) in enumerate(MOEDAS, start=1):
        linhas.append(f"  {i} - {nome} ({cod})")
    return "\n".join(linhas)


def responder(mensagem):
    try:
        if mensagem == "MENU":
            return gerar_menu()

        if mensagem.startswith("ESCOLHA;"):
            n = int(mensagem.split(";", 1)[1])
            if not (1 <= n <= len(MOEDAS)):
                return "ERRO: opcao invalida. Escolha um numero da lista."
            cod, nome = MOEDAS[n - 1]
            return f"Digite o valor em reais (R$) a converter para {nome} ({cod}):"

        if mensagem.startswith("CONVERTE;"):
            _, n_str, valor_str = mensagem.split(";", 2)
            n = int(n_str)
            if not (1 <= n <= len(MOEDAS)):
                return "ERRO: opcao invalida."
            valor = float(valor_str.replace(",", ".").strip())
            cod, nome = MOEDAS[n - 1]
            cotacao, data_hora = consultar_ptax(cod)
            convertido = valor / cotacao
            casas = 4 if convertido >= 0.01 else 8
            return (f"R$ {valor:.2f} = {convertido:.{casas}f} {cod} "
                    f"(PTAX compra: 1 {cod} = R$ {cotacao:.4f} | {data_hora})")

        return "ERRO: comando desconhecido."
    except ValueError:
        return "ERRO: entrada invalida (numero/valor)."
    except Exception as e:
        return f"ERRO ao consultar a cotacao: {e}"


def atender_cliente(conexao, endereco):
    print(f"[TCP] Cliente conectado: {endereco}")
    with conexao:
        while True:
            dados = conexao.recv(1024)
            if not dados:
                break
            mensagem = dados.decode("utf-8")
            print(f"[TCP] {endereco}: {mensagem!r}")
            resposta = responder(mensagem)
            conexao.sendall(resposta.encode("utf-8"))
    print(f"[TCP] Cliente desconectado: {endereco}\n")


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(1)
    print(f"[TCP] Servidor (menu + PTAX) ouvindo em {HOST}:{PORT} ...")
    print("[TCP] Pressione Ctrl+C para encerrar.\n")
    try:
        while True:
            conexao, endereco = servidor.accept()
            atender_cliente(conexao, endereco)
    except KeyboardInterrupt:
        print("\n[TCP] Servidor encerrado.")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
