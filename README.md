# jarvis-cv

O assistente chama-se **Truta** (muda em `config.py` → `ASSISTENTE`).

Assistente pessoal ao estilo JARVIS, feito em Cabo Verde, a correr no **Fedora**.
Objetivo: um assistente que ouve, fala em **português (e um dia em crioulo)** e age no mundo real: PC, Smart TV, telemóvel.

## Arrancar sozinho com o Fedora 🚀

```bash
./arranque.sh instalar     # o Truta passa a arrancar sempre que entras na sessão
./arranque.sh registos     # ver o que ele está a fazer
./arranque.sh reiniciar    # depois de um git pull
./arranque.sh parar        # parar agora (para testar no terminal, por exemplo)
./arranque.sh remover      # desligar o arranque automático
```

Só pode haver um Truta a ouvir de cada vez: se o serviço estiver ligado e correres
`python3 jarvis.py`, ele avisa e sai. Dizer "desliga" deixa-o parado até ao próximo login.

## Estado atual — Fase 3: cérebro com IA 🧠

Pedidos compostos ou livres ("abre o YouTube e pesquisa algo interessante sobre IA",
"conta-me uma curiosidade sobre Cabo Verde") vão para uma IA na nuvem.
Comandos simples continuam a ser resolvidos localmente, sem internet.

**Configurar (uma vez):**

1. Cria uma chave grátis em <https://aistudio.google.com> → *Get API key*.
2. Copia o ficheiro de exemplo e mete lá a chave:
   ```bash
   cp .env.exemplo .env
   nano .env          # GEMINI_API_KEY=a_tua_chave
   ```
   O `.env` nunca vai para o GitHub.
3. Testa só o cérebro:
   ```bash
   python3 cerebro.py --verificar   # diagnostica a chave (sem a mostrar)
   python3 cerebro.py "abre o youtube e pesquisa algo interessante sobre IA"
   ```

A IA só pode pedir ações de uma **lista fechada** (`ACOES_PERMITIDAS` em `cerebro.py`):
abrir sites, pesquisar, abrir apps, volume, bloquear ecrã. Nunca executa comandos livres.
Para usar o Claude em vez do Gemini, muda `IA` e `MODELO_IA` em `config.py`.

## Fase 2: comandos de voz 🎙️

Duas palmas → o JARVIS diz *"Sim, Landim?"* → dizes uma ordem → ele executa.

```bash
pip install --user -r requirements.txt
python3 jarvis.py              # palmas + voz
python3 jarvis.py --escrever   # testar os comandos escrevendo no teclado
python3 ouvido.py              # testar só o reconhecimento de voz (4 s)
```

Na primeira vez descarrega o modelo Whisper (~480 MB). Se for lento,
troca `MODELO_WHISPER` para `"base"` em `config.py`.

**Comandos que já percebe**

| Diz… | Faz |
|---|---|
| "abre o YouTube / GitHub / Gmail / WhatsApp / Google" | abre o site |
| "abre o VS Code / terminal / navegador / ficheiros" | abre a aplicação |
| "aumenta / baixa o volume", "silêncio" | controla o som |
| "bloqueia o ecrã" | bloqueia o PC |
| "bom dia" / "boa tarde" / "resumo do dia" | ☀️ resumo: data, tempo na Praia e dica do dia |
| "que horas são", "que dia é hoje" | responde em voz |
| "pesquisa por …" | pesquisa no Google |
| "modo trabalho" | VS Code + terminal + GitHub |
| "obrigado", "quem és tu" | conversa |
| "desliga", "adeus" | encerra o JARVIS |

Os comandos estão em `comandos.py`; os testes em `tests/` (`python3 -m pytest tests`).

## Fase 1: duas palmas 👏👏

Bates duas palmas e o JARVIS cumprimenta-te em voz e abre o ambiente de trabalho
(VS Code, terminal e GitHub).

### Instalação (Fedora)

```bash
sudo dnf install portaudio speech-dispatcher espeak-ng
pip install --user -r requirements.txt
```

### Voz brasileira (Piper)

Voz neural, gratuita e offline. Descarrega-se sozinha na primeira vez que o JARVIS fala (~60 MB). Também podes descarregar à mão:

```bash
python3 -m piper.download_voices pt_BR-faber-medium --data-dir vozes
python3 voz.py                       # ouve a voz
python3 voz.py "Qualquer frase"      # testa uma frase tua
```

Sem a voz descarregada, o JARVIS usa o espeak (robótico) como reserva.
Para trocar de voz, muda `VOZ` no topo de `voz.py`.

### Calibrar o microfone (faz isto primeiro)

```bash
python3 jarvis_palmas.py --calibrar
```

Aparece uma barra com o volume em tempo real.

1. Bate palmas e anota o valor (ex.: `0.60`).
2. Fala normalmente e anota o valor (ex.: `0.15`).
3. No topo de `jarvis_palmas.py`, mete o `LIMIAR` entre os dois (ex.: `0.40`).

- Dispara com barulhos? → sobe o `LIMIAR`.
- Não apanha as palmas? → desce o `LIMIAR`.

### Usar

```bash
python3 jarvis_palmas.py
```

Para mudar o que acontece, edita a função `modo_trabalho()`.

## Roteiro

Ver [ROADMAP.md](ROADMAP.md).
