"""
Servidor UDP - Conversor de Moedas (menu + cotacao REAL via API PTAX do BCB)
Sistemas Distribuidos

O SERVIDOR conduz o dialogo por um protocolo simples de 3 mensagens:
  1) cliente envia "MENU"                  -> servidor devolve a lista numerada
  2) cliente envia "ESCOLHA;<n>"           -> servidor valida e devolve a
                                              pergunta pedindo o valor em R$
  3) cliente envia "CONVERTE;<n>;<valor>"  -> servidor consulta a PTAX e devolve
                                              o resultado da conversao
Como cada mensagem carrega tudo o que o servidor precisa, ele permanece SEM
ESTADO (stateless) - ideal para UDP, que e nao orientado a conexao.

Obs.: consulta olinda.bcb.gov.br via HTTPS; precisa de internet na maquina.
"""

import socket
import json
import urllib.request
import urllib.parse
from datetime import date, timedelta

HOST = "192.168.86.33" # #IP do Servidor
PORT = 8888

# Lista ORDENADA de moedas disponiveis (o numero do menu e o indice+1).
# (codigo PTAX, nome exibido)
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
    """Retorna (cotacao_compra, data_hora). Tenta ate 10 dias para tras porque a
    PTAX so publica em dias uteis (fim de semana/feriado retornam value vazio)."""
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
    """Interpreta a mensagem do cliente e devolve a resposta (protocolo de 3 msgs)."""
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


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.bind((HOST, PORT))
    print(f"[UDP] Servidor (menu + PTAX) ouvindo em {HOST}:{PORT} ...")
    print("[UDP] Pressione Ctrl+C para encerrar.\n")
    try:
        while True:
            dados, endereco = servidor.recvfrom(1024)
            mensagem = dados.decode("utf-8")
            print(f"[UDP] {endereco}: {mensagem!r}")
            resposta = responder(mensagem)
            servidor.sendto(resposta.encode("utf-8"), endereco)
    except KeyboardInterrupt:
        print("\n[UDP] Servidor encerrado.")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
