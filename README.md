# jarvis-cv

Assistente pessoal ao estilo JARVIS, feito em Cabo Verde, a correr no **Fedora**.
Objetivo: um assistente que ouve, fala em **português (e um dia em crioulo)** e age no mundo real: PC, Smart TV, telemóvel.

## Estado atual — Fase 1: duas palmas 👏👏

Bates duas palmas e o JARVIS cumprimenta-te em voz e abre o ambiente de trabalho
(VS Code, terminal e GitHub).

### Instalação (Fedora)

```bash
sudo dnf install portaudio speech-dispatcher espeak-ng
pip install --user -r requirements.txt
```

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
