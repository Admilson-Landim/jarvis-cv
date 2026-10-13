"""
"Bom dia, JARVIS": resumo do dia falado.

Junta a hora, a data e o tempo na Praia. Se o cérebro (IA) estiver ligado,
ele transforma isso num resumo natural e junta uma dica do dia para programadores.
Sem IA (ou sem internet), usa um texto fixo.

Teste isolado:
    python3 resumo.py
"""

import time

import tempo
from config import NOME

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def saudacao(hora: int) -> str:
    return "Bom dia" if 5 <= hora < 12 else "Boa tarde" if 12 <= hora < 19 else "Boa noite"


def dados_do_dia(agora: time.struct_time | None = None) -> dict:
    agora = agora or time.localtime()
    return {
        "saudacao": saudacao(agora.tm_hour),
        "hora": f"{agora.tm_hour} e {agora.tm_min:02d}",
        "data": f"{DIAS[agora.tm_wday]}, {agora.tm_mday} de {MESES[agora.tm_mon - 1]}",
        "tempo": tempo.obter(),
    }


def resumo_simples(d: dict) -> str:
    texto = f"{d['saudacao']}, {NOME}. Hoje é {d['data']} e são {d['hora']}."
    if d["tempo"]:
        texto += " " + tempo.frase(d["tempo"])
    return texto


def gerar(cerebro=None) -> str:
    d = dados_do_dia()
    if cerebro is None:
        return resumo_simples(d)

    meteo = tempo.frase(d["tempo"]) if d["tempo"] else "sem dados do tempo (sem internet)"
    pedido = (
        f"Faz o resumo do dia do {NOME}, para ser falado, em 4 a 5 frases curtas. "
        f"Começa com '{d['saudacao']}, {NOME}'. Usa SÓ estes dados, sem inventar notícias: "
        f"data: {d['data']}; hora: {d['hora']}; tempo: {meteo}. "
        "Se o tempo pedir, dá uma sugestão prática (água, guarda-chuva, protetor solar). "
        "Termina com uma dica curta e útil do dia para um programador (ferramenta, hábito ou conceito). "
        "Sem ações."
    )
    texto = cerebro.escrever(pedido)
    return texto or resumo_simples(d)


if __name__ == "__main__":
    import cerebro as c
    print(gerar(c.Cerebro() if c.disponivel() else None))
