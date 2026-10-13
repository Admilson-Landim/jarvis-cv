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

from config import IA, MODELO_IA, MODELOS_RESERVA, NOME, TEMPO_IA

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
- Escreve em português correto, COM acentos (é, ã, ç...), porque o texto vai ser lido em voz alta.
- Pedidos compostos ("abre X e pesquisa Y") viram várias ações, pela ordem.
- Não repitas: "pesquisar_youtube" já abre o YouTube, por isso não juntes "abrir_site" do YouTube.
- Se pedirem para escolheres um tema ("algo interessante"), escolhe tu um termo concreto.
- Perguntas de conhecimento ("quem foi...", "o que é...") respondes só com a voz, SEM ações.
  Só pesquisas ou abres algo quando ele pedir explicitamente.
- Se pedirem algo que não está na lista, diz com simpatia que ainda não sabes fazer isso."""


# --- Chaves ------------------------------------------------------------------
def _ler_env() -> list:
    """Devolve [(nome, valor, nº da linha)] do .env, limpando espaços e aspas."""
    env = PASTA / ".env"
    if not env.exists():
        return []
    entradas = []
    texto = env.read_text(encoding="utf-8-sig")  # ignora BOM invisível
    for n, linha in enumerate(texto.splitlines(), 1):
        linha = linha.strip().removeprefix("export ").strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            limpo = "".join(c for c in valor if 33 <= ord(c) <= 126).strip('"').strip("'")
            sujo = len(limpo) != len(valor.strip().strip('"').strip("'"))  # havia espaços/invisíveis
            entradas.append((chave.strip(), limpo, n, sujo))
    return entradas


def _carregar_env() -> None:
    # O .env manda: a última linha válida de cada chave ganha
    for chave, valor, _, _ in _ler_env():
        if valor and "cola_aqui" not in valor:
            os.environ[chave] = valor


_carregar_env()

NOME_CHAVE = {"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY"}


def _mascarar(valor: str) -> str:
    return f"{valor[:4]}…{valor[-4:]} ({len(valor)} caracteres)" if len(valor) > 10 else "(curta demais)"


def verificar() -> None:
    """Diagnóstico da chave sem a mostrar inteira."""
    nome = NOME_CHAVE[IA]
    print(f"IA: {IA} | modelo: {MODELO_IA} | chave esperada: {nome}")
    if not (PASTA / ".env").exists():
        print("❌ Não existe ficheiro .env nesta pasta.")
        return
    linhas = [(v, n, sujo) for c, v, n, sujo in _ler_env() if c == nome]
    if not linhas:
        print(f"❌ O .env não tem nenhuma linha {nome}=...")
        return
    for valor, n, sujo in linhas:
        aviso = "  ⚠️ ainda é o texto de exemplo" if "cola_aqui" in valor else ""
        if sujo:
            aviso += "  (tinha espaços ou caracteres invisíveis — já os ignoro)"
        print(f"  linha {n}: {_mascarar(valor)}{aviso}")
    if len(linhas) > 1:
        print("⚠️ Há mais do que uma linha com a chave; vale a última válida. Melhor deixar só uma.")
    usada = os.environ.get(nome, "")
    print(f"→ chave em uso: {_mascarar(usada) if usada else 'nenhuma'}")
    if not usada:
        return
    try:
        resposta = PROVEDORES[IA]([{"role": "user", "content": "Diz olá numa frase curta."}])
        print(f"✅ A IA aceitou a chave (modelo usado: {ultimo_modelo}). Está tudo pronto!")
        print(f"   resposta: {analisar(resposta)['resposta']}")
    except urllib.error.HTTPError as erro:
        print(f"❌ A IA respondeu com erro {erro.code}: {erro.read().decode(errors='ignore')[:300]}")
    except Exception as erro:
        print(f"❌ Não consegui contactar a IA: {erro}")


def disponivel() -> bool:
    return bool(os.environ.get(NOME_CHAVE.get(IA, ""), ""))


# --- Pedidos às IAs ----------------------------------------------------------
def _post(url: str, cabecalhos: dict, corpo: dict, timeout: float = 30) -> dict:
    pedido = urllib.request.Request(
        url, data=json.dumps(corpo).encode(), method="POST",
        headers={"Content-Type": "application/json", **cabecalhos},
    )
    with urllib.request.urlopen(pedido, timeout=timeout) as r:
        return json.loads(r.read())


ESTADO = PASTA / ".estado.json"  # guarda o último modelo que funcionou (não vai para o git)


def _ler_estado() -> dict:
    try:
        return json.loads(ESTADO.read_text())
    except Exception:
        return {}


def _gravar_estado(**valores) -> None:
    try:
        ESTADO.write_text(json.dumps({**_ler_estado(), **valores}))
    except OSError:
        pass


ultimo_modelo = _ler_estado().get("modelo", "")
ERROS_FATAIS = (400, 401, 403)  # chave ou pedido inválido: outro modelo não resolve


def _gemini(historico: list) -> str:
    global ultimo_modelo
    contents = [{"role": "model" if m["role"] == "assistant" else "user",
                 "parts": [{"text": m["content"]}]} for m in historico]
    corpo = {
        "systemInstruction": {"parts": [{"text": _instrucoes()}]},
        "contents": contents,
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7},
    }
    # Começa pelo último modelo que funcionou (evita esperar pelos que estão ocupados)
    ordem = [MODELO_IA] + [m for m in MODELOS_RESERVA if m != MODELO_IA]
    modelos = ([ultimo_modelo] if ultimo_modelo in ordem else []) + [m for m in ordem if m != ultimo_modelo]
    ultimo_erro = None
    for modelo in modelos:
        try:
            dados = _post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                {"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
                corpo,
                timeout=TEMPO_IA,
            )
        except urllib.error.HTTPError as erro:
            if erro.code in ERROS_FATAIS:
                raise
            print(f"  ({modelo} indisponível ({erro.code}), a tentar outro...)")
            ultimo_erro = erro
            continue
        except (TimeoutError, urllib.error.URLError) as erro:
            print(f"  ({modelo} não respondeu a tempo, a tentar outro...)")
            ultimo_erro = erro
            continue
        if modelo != ultimo_modelo:
            print(f"  (a usar {modelo})")
            _gravar_estado(modelo=modelo)
        ultimo_modelo = modelo
        partes = dados["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in partes)
    raise ultimo_erro


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
            if erro.code >= 500 or erro.code == 404:
                return {"resposta": "Os servidores da IA estão ocupados. Tenta daqui a pouco.", "acoes": []}
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
    if sys.argv[1:] == ["--verificar"]:
        verificar()
        sys.exit(0)
    if not disponivel():
        print(f"Falta a chave {NOME_CHAVE[IA]} no ficheiro .env")
        sys.exit(1)
    pedido = " ".join(sys.argv[1:]) or "Olá JARVIS, quem és tu?"
    print(json.dumps(Cerebro().pensar(pedido), ensure_ascii=False, indent=2))
