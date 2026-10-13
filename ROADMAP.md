# Roteiro do jarvis-cv

Cada fase termina com algo que se pode testar no Fedora.

## Fase 1 — Duas palmas ✅ (concluída)
- [x] Deteção de duas palmas pelo microfone
- [x] Saudação em voz consoante a hora
- [x] Abrir VS Code, terminal e GitHub
- [x] Calibração confirmada no PC do Admilson (LIMIAR 0.45)
- [x] Teste real: duas palmas abrem o ambiente (1 palma não dispara)

## Fase 2 — Ouvir comandos em português ✅ (concluída)
- [x] Voz natural: Piper pt_BR (faber) — aprovada pelo Landim
- [x] Depois das palmas, "Sim, Landim?" e escuta da ordem (Whisper offline)
- [x] Comandos: abrir sites/apps, volume, bloquear ecrã, horas/data, pesquisa, modo trabalho
- [x] Modo `--escrever` e testes automáticos dos comandos
- [x] Teste real: palmas → "abre YouTube" → abriu (Whisper small percebe bem)
- [x] Bip depois de "Sim, Landim?" para saber quando falar

## Fase 3 — Cérebro (LLM) ✅ (base concluída)
- [x] Gemini grátis (gemini-3.5-flash-lite), Claude como alternativa em config.py
- [x] A IA devolve resposta + ações de uma lista fechada (nada de comandos livres)
- [x] Comandos simples ficam locais; compostos/livres/desconhecidos vão à IA
- [x] Memória curta da conversa (últimas mensagens)
- [x] Teste real: "abre o YouTube e pesquisa algo interessante sobre IA", lo-fi, Amílcar Cabral, curiosidade CV
- [x] Modelos de reserva + lembrar o modelo que funcionou + espera de 8 s por modelo
- [x] Memória curta testada ("quem foi Amílcar Cabral?" → "e onde é que ele nasceu?")
- [x] Último modelo que funcionou fica gravado em .estado.json
- [ ] "Bom dia, JARVIS": hora, tempo na Praia, notícias
- [ ] Ações perigosas pedem confirmação

## Fase 4 — Smart TV (TOP VISION)
- [ ] Descobrir o sistema da TV e como controlá-la pela rede
- [ ] Palmas → ligar a TV / abrir YouTube; volume por voz

## Fase 5 — Extras
- [ ] Comandos em crioulo cabo-verdiano
- [ ] Ligação ao DonaGerma (pacotes de dados por voz)
- [ ] Interface com a esfera animada
