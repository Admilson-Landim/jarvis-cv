"""Configuração pessoal do JARVIS."""

NOME = "Landim"   # como o JARVIS te chama

# Navegador para abrir sites ("brave-browser", "firefox"...). None = o padrão do sistema
NAVEGADOR = "brave-browser"

# Cérebro (IA na nuvem). A chave vai no ficheiro .env
IA = "gemini"                       # "gemini" (grátis) ou "claude" (API paga)
MODELO_IA = "gemini-3.5-flash-lite"  # rápido; "gemini-3.8-flash" é mais esperto
# Se o modelo principal estiver ocupado, tenta estes por ordem (só Gemini)
MODELOS_RESERVA = ["gemini-3.8-flash", "gemini-3.1-flash-lite", "gemini-3.6-flash"]
# Para o Claude: IA = "claude" e MODELO_IA = "claude-haiku-5-5"

# Reconhecimento de voz (Whisper): "base" é mais rápido, "small" percebe melhor
MODELO_WHISPER = "small"

# Escuta do comando depois das palmas
LIMIAR_VOZ = 0.05        # pico a partir do qual conta como "estás a falar"
SILENCIO_FIM = 1.2       # s de silêncio depois de falares = fim do comando
ESPERA_MAX = 4.0         # s à espera que comeces a falar
DURACAO_MAX = 8.0        # s máximos de gravação
