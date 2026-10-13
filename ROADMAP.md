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
- [x] "Bom dia, JARVIS": data, hora, tempo na Praia (Open-Meteo) e dica do dia pela IA
- [x] Teste real do "Boa tarde": tempo real da Praia, conselho da água e dica do dia
- [x] Palmas corrigidas no jarvis.py (microfone a 48 kHz, igual à calibração)
- [x] Assistente renomeado para "Truta" (config.py)
- [ ] Ações perigosas pedem confirmação

## Fase 3.5 — Integração com o Fedora
- [x] Serviço systemd do utilizador (`arranque.sh`): arranca no login, reinicia se falhar
- [x] Só uma instância a ouvir o microfone; notificação do GNOME quando fica pronto
- [x] Serviço instalado e a funcionar no PC do Landim (palmas + "Abre o Github" sem terminal)
- [ ] Teste real: terminar a sessão, voltar a entrar e o Truta arrancar sozinho
- [x] IA gratuita instável: "Um momento" se demorar, última tentativa, e plano B local

## Fase 4 — Smart TV (TOP VISION)
- [x] `descobrir_tv.py`: procura TVs (SSDP/UPnP) e testa portas de controlo conhecidas
- [x] TV TOP VISION: Android com launcher próprio (Play Store, Kindlink, GAIA)
- [x] Atenção: 192.168.88.19 (porta 5555) é o Huawei PPA-LX2 do Landim, NÃO a TV
- [x] IP da TV: **192.168.88.16** (MAC Wi-Fi 20:9B:E6:D6:C9:3B confirmado nas definições)
- [x] TV: Android 11, modelo "SMART_TV", firmware 20220914, 1,5 GB RAM, GPU Mali-G52
- [ ] **Retomar aqui:** o menu da TV não mostra Opções de programador. Tentar: (1) 7 toques em
      "Versão do Firmware"/"Versão Android" em Info do sistema; (2) app "Activity Launcher" da
      Play Store para abrir as Definições Android escondidas; (3) `nmap -p- 192.168.88.16`
- [x] Tentado: 10+ toques em "Versão do Firmware" (nada); `nmap -p-` com a TV no menu e com o
      YouTube aberto: todas as portas TCP fechadas
- [x] Activity Launcher não existe na Play Store da TV (versão TV). Existe no F-Droid
      (de.szalkowski.activitylauncher), mas a pen USB não foi reconhecida e o gestor de
      ficheiros instalado não abriu. **Em pausa** — retomar com: APK pelo OPEN BROWSER da TV
      (f-droid.org), outra pen USB (FAT32), ou plano C (infravermelhos)
- [ ] Ativar depuração USB / sem fios na TV
- [ ] Plano C se não houver ADB: emissor de infravermelhos (Wi-Fi/USB) a imitar o comando
- [ ] `adb connect <IP da TV>:5555`, confirmar modelo e encontrar o pacote do YouTube
- [ ] Palmas → ligar a TV / abrir YouTube; volume por voz

## Fase 5 — Extras
- [ ] "Truta, programa o projeto X": lança o Claude Code numa pasta autorizada para seguir
      um PLANO.md por ordem — com confirmação por voz antes de arrancar
- [ ] Comandos em crioulo cabo-verdiano
- [ ] Ligação ao DonaGerma (pacotes de dados por voz)
- [ ] Controlar o telemóvel Huawei por ADB (ex.: ler a última notificação)
- [ ] Interface com a esfera animada
