#!/usr/bin/env bash
# Põe o Truta a arrancar sozinho quando entras no Fedora (serviço systemd do utilizador).
#
#   ./arranque.sh instalar     # ativa e arranca já
#   ./arranque.sh estado       # está a correr?
#   ./arranque.sh registos     # ver o que o Truta está a fazer (Ctrl+C para sair)
#   ./arranque.sh parar        # para agora (volta no próximo login)
#   ./arranque.sh reiniciar    # depois de um git pull
#   ./arranque.sh remover      # desativa o arranque automático
set -euo pipefail

SERVICO="truta"
PASTA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FICHEIRO="$HOME/.config/systemd/user/$SERVICO.service"

case "${1:-}" in
  instalar)
    mkdir -p "$(dirname "$FICHEIRO")"
    cat > "$FICHEIRO" <<EOF
[Unit]
Description=Truta - assistente de voz
# Só arranca dentro da sessão gráfica (precisa de som, do browser e do ecrã)
PartOf=graphical-session.target
After=graphical-session.target pipewire.service wireplumber.service

[Service]
Type=simple
ExecStart=/bin/bash -c 'cd "$PASTA" && exec /usr/bin/python3 -u jarvis.py'
# Se falhar, tenta outra vez; se disseres "desliga", fica desligado até ao próximo login
Restart=on-failure
RestartSec=10

[Install]
WantedBy=graphical-session.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now "$SERVICO"
    echo "✅ Truta instalado. Vai arrancar sozinho sempre que entrares no Fedora."
    echo "   Ver o que está a fazer: ./arranque.sh registos"
    ;;
  estado)    systemctl --user status "$SERVICO" --no-pager ;;
  registos)  journalctl --user -u "$SERVICO" -f -n 30 ;;
  parar)     systemctl --user stop "$SERVICO" && echo "Truta parado." ;;
  reiniciar) systemctl --user restart "$SERVICO" && echo "Truta reiniciado." ;;
  remover)
    systemctl --user disable --now "$SERVICO" 2>/dev/null || true
    rm -f "$FICHEIRO"
    systemctl --user daemon-reload
    echo "Arranque automático removido."
    ;;
  *)
    sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
