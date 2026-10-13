"""Configuração pessoal do JARVIS."""

NOME = "Landim"   # como o JARVIS te chama

# Navegador para abrir sites ("brave-browser", "firefox"...). None = o padrão do sistema
NAVEGADOR = "brave-browser"

# Reconhecimento de voz (Whisper): "base" é mais rápido, "small" percebe melhor
MODELO_WHISPER = "small"

# Escuta do comando depois das palmas
LIMIAR_VOZ = 0.05        # pico a partir do qual conta como "estás a falar"
SILENCIO_FIM = 1.2       # s de silêncio depois de falares = fim do comando
ESPERA_MAX = 4.0         # s à espera que comeces a falar
DURACAO_MAX = 8.0        # s máximos de gravação
