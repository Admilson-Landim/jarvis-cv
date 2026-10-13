"""
Cérebro do JARVIS: manda o pedido a uma IA na nuvem, que devolve
o que dizer e uma lista de ações (sempre de uma lista fechada e segura).

IA escolhida em config.py (IA = "gemini" ou "claude").
A chave fica no ficheiro .env (nunca vai para o GitHub):
    GEMINI_API_KEY=...
    ANTHROPIC_API_KEY=...

Teste isolado:
    python3 cerebro.py "abre o youtube e pesquisa algo sobre IA"
"""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from config import IA, MODELO_IA, NOME

PASTA = Path(__file__).parent

# Ações que a IA pode pedir. Nada fora desta lista é executado.
ACOES_PERMITIDAS = {
    "abrir_site": "abre um site. Campos: url (https://...)",
    "pesquisar_google": "pesquisa no Google. Campos: termo",
    "pesquisar_youtube": "pesquisa vídeos no YouTube. Campos: termo",
    "abrir_app": "abre uma aplicação. Campos: app (vscode | terminal | navegador | ficheiros)",
    "volume": "muda o volume. Campos: direcao (mais | menos | mudo)",
    "bloquear_ecra": "bloqueia o computador. Sem campos",
    "modo_trabalho": "abre VS Code, terminal e GitHub. Sem campos",
    "sair": "desliga o JARVIS. Sem campos",
}


def _instrucoes() -> str:
    lista = "\n".join(f'- "{nome}": {desc}' for nome, desc in ACOES_PERMITIDAS.items())
    agora = time.strftime("%d/%m/%Y %H:%M")
    return f"""És o JARVIS, o assistente pessoal de voz do {NOME}, um programador de Cabo Verde.
Corres no PC dele (Fedora Linux). Agora são {agora}.

Responde SEMPRE só com JSON neste formato:
{{"resposta": "o que vais dizer em voz alta", "acoes": [{{"tipo": "...", ...}}]}}

Regras:
- "resposta" em português, curta (1 a 3 frases), natural para ser falada. Sem emojis, markdown ou links.
- Trata-o por {NOME}, com um toque de humor britânico do JARVIS, sem exagerar.
- "acoes" só pode usar estes tipos (lista vazia se for só conversa):
{lista}
- Pedidos compostos ("abre X e pesquisa Y") viram várias ações, pela ordem.
- Se pedirem para escolheres um tema ("algo interessante"), escolhe tu um termo concreto.
- Se pedirem algo que não está na lista, diz com simpatia que ainda não sabes fazer isso."""


# --- Chaves ------------------------------------------------------------------
def _carregar_env() -> None:
    env = PASTA / ".env"
    if not env.exists():
        return
    for linha in env.read_text().splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


_carregar_env()

NOME_CHAVE = {"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY"}


def disponivel() -> bool:
    return bool(os.environ.get(NOME_CHAVE.get(IA, ""), ""))


# --- Pedidos às IAs ----------------------------------------------------------
def _post(url: str, cabecalhos: dict, corpo: dict) -> dict:
    pedido = urllib.request.Request(
        url, data=json.dumps(corpo).encode(), method="POST",
        headers={"Content-Type": "application/json", **cabecalhos},
    )
    with urllib.request.urlopen(pedido, timeout=20) as r:
        return json.loads(r.read())


def _gemini(historico: list) -> str:
    contents = [{"role": "model" if m["role"] == "assistant" else "user",
                 "parts": [{"text": m["content"]}]} for m in historico]
    dados = _post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_IA}:generateContent",
        {"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
        {
            "systemInstruction": {"parts": [{"text": _instrucoes()}]},
            "contents": contents,
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7},
        },
    )
    partes = dados["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in partes)


def _claude(historico: list) -> str:
    dados = _post(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
        {"model": MODELO_IA, "max_tokens": 600, "system": _instrucoes(), "messages": historico},
    )
    return "".join(b.get("text", "") for b in dados["content"] if b.get("type") == "text")


PROVEDORES = {"gemini": _gemini, "claude": _claude}


# --- Interpretar a resposta --------------------------------------------------
def analisar(texto: str) -> dict:
    """Lê o JSON da IA e deixa passar só ações permitidas e bem formadas."""
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.strip("`").removeprefix("json").strip()
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError:
        return {"resposta": texto[:300], "acoes": []}  # respondeu em texto simples

    acoes = []
    for acao in dados.get("acoes") or []:
        if not isinstance(acao, dict) or acao.get("tipo") not in ACOES_PERMITIDAS:
            continue
        if acao["tipo"] == "abrir_site" and not str(acao.get("url", "")).startswith(("https://", "http://")):
            continue
        acoes.append(acao)
    return {"resposta": str(dados.get("resposta", "")).strip(), "acoes": acoes}


class Cerebro:
    def __init__(self, memoria: int = 6):
        self.historico: list = []
        self.memoria = memoria  # mensagens recentes guardadas para dar contexto

    def pensar(self, pedido: str) -> dict:
        self.historico.append({"role": "user", "content": pedido})
        self.historico = self.historico[-self.memoria:]
        try:
            bruto = PROVEDORES[IA](self.historico)
        except urllib.error.HTTPError as erro:
            detalhe = erro.read().decode(errors="ignore")[:200]
            print(f"  (erro da IA {erro.code}: {detalhe})")
            self.historico.pop()
            if erro.code == 429:
                return {"resposta": "Atingi o limite gratuito da IA. Tenta daqui a pouco.", "acoes": []}
            return {"resposta": "A IA recusou o pedido. Vê a mensagem no terminal.", "acoes": []}
        except Exception as erro:
            print(f"  (sem ligação à IA: {erro})")
            self.historico.pop()
            return {"resposta": "Não consegui falar com o meu cérebro na nuvem.", "acoes": []}

        resultado = analisar(bruto)
        self.historico.append({"role": "assistant", "content": json.dumps(resultado, ensure_ascii=False)})
        return resultado


if __name__ == "__main__":
    import sys
    if not disponivel():
        print(f"Falta a chave {NOME_CHAVE[IA]} no ficheiro .env")
        sys.exit(1)
    pedido = " ".join(sys.argv[1:]) or "Olá JARVIS, quem és tu?"
    print(json.dumps(Cerebro().pensar(pedido), ensure_ascii=False, indent=2))
