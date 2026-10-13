# Notas para o Claude

- O dono é o Admilson (Cabo Verde); o JARVIS trata-o por "Landim" (config.py). Fala com ele em português.
- O código corre no **Fedora Workstation** do Admilson; o Claude implementa e faz push,
  o Admilson faz `git pull`, testa e reporta. Escreve sempre instruções de teste claras.
- Trabalhar por fases (ver ROADMAP.md); atualizar o ROADMAP ao terminar cada passo.
- Python 3, dependências em `requirements.txt`, pacotes do sistema via `dnf`.
- O ambiente do Claude não tem microfone nem altifalante: validar com testes/lógica,
  e deixar a verificação real (áudio, TV) para o Admilson.
- Segurança: a IA só pode pedir ações de `ACOES_PERMITIDAS` (cerebro.py), validadas em `analisar()`.
  Nunca dar à IA execução de comandos livres. Chaves só no `.env` (ignorado pelo git).
