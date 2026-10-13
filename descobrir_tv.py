#!/usr/bin/env python3
"""
Detetive de TVs: procura dispositivos na rede (SSDP/UPnP) e testa as portas
de controlo conhecidas, para sabermos como falar com a TV.

Uso (com a TV ligada e na mesma rede Wi-Fi do PC):
    python3 descobrir_tv.py
    python3 descobrir_tv.py 192.168.88.50     # se já souberes o IP da TV
"""

import re
import socket
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# Portas que denunciam o sistema da TV
PORTAS = {
    5555: "ADB por rede (Android TV / Google TV, se a depuração estiver ligada)",
    6466: "Android TV Remote (Android TV / Google TV)",
    6467: "Android TV Remote — emparelhamento",
    8008: "Google Cast / Chromecast",
    8009: "Google Cast / Chromecast",
    8001: "Samsung Tizen (API remota)",
    8002: "Samsung Tizen (API remota segura)",
    3000: "LG webOS",
    3001: "LG webOS (segura)",
    36669: "Hisense / VIDAA (MQTT)",
    56789: "VIDAA / Hisense (algumas versões)",
    7676: "UPnP / DLNA (comum em muitas TVs)",
    1925: "Philips (JointSpace)",
    1926: "Philips (JointSpace segura)",
}


def ssdp_procurar(espera: float = 3.0) -> dict:
    """Pergunta à rede quem responde a UPnP. Devolve {ip: [respostas]}."""
    pedido = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
              'MAN: "ssdp:discover"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n').encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    s.settimeout(espera)
    s.sendto(pedido, ("239.255.255.250", 1900))
    encontrados: dict = {}
    try:
        while True:
            dados, (ip, _) = s.recvfrom(4096)
            encontrados.setdefault(ip, []).append(dados.decode(errors="ignore"))
    except socket.timeout:
        pass
    finally:
        s.close()
    return encontrados


def cabecalho(resposta: str, nome: str) -> str:
    m = re.search(rf"^{nome}:\s*(.+)$", resposta, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else ""


def descrever_dispositivo(location: str) -> dict:
    """Lê a ficha UPnP (XML) do dispositivo: nome, fabricante, modelo."""
    try:
        with urllib.request.urlopen(location, timeout=3) as r:
            xml = r.read().decode(errors="ignore")
    except Exception:
        return {}
    campos = {}
    for tag in ("friendlyName", "manufacturer", "modelName", "modelNumber"):
        m = re.search(rf"<{tag}>([^<]*)</{tag}>", xml)
        if m:
            campos[tag] = m.group(1).strip()
    return campos


def portas_abertas(ip: str) -> list:
    def testar(porta):
        try:
            with socket.create_connection((ip, porta), timeout=1.0):
                return porta
        except OSError:
            return None
    with ThreadPoolExecutor(max_workers=len(PORTAS)) as ex:
        return sorted(p for p in ex.map(testar, PORTAS) if p)


def palpite(portas: list, texto: str) -> str:
    t = texto.lower()
    if 6466 in portas or 5555 in portas or "android" in t or "google" in t:
        return "Android TV / Google TV 👍 (controlo completo possível)"
    if 8001 in portas or 8002 in portas or "samsung" in t:
        return "Samsung Tizen"
    if 3000 in portas or 3001 in portas or "webos" in t or "lg electronics" in t:
        return "LG webOS"
    if 36669 in portas or "vidaa" in t or "hisense" in t:
        return "VIDAA / Hisense"
    if 8008 in portas or 8009 in portas:
        return "Tem Chromecast integrado (dá para enviar YouTube)"
    if 7676 in portas or "mediarenderer" in t:
        return "Só DLNA (dá para enviar vídeos/música, controlo limitado)"
    return "Desconhecido"


def analisar_ip(ip: str, respostas: list) -> None:
    texto = "\n".join(respostas)
    ficha = {}
    for r in respostas:
        loc = cabecalho(r, "LOCATION")
        if loc:
            ficha = descrever_dispositivo(loc)
            if ficha:
                break
    servidor = next((cabecalho(r, "SERVER") for r in respostas if cabecalho(r, "SERVER")), "")
    portas = portas_abertas(ip)
    texto_total = texto + " " + " ".join(ficha.values())

    print(f"\n📍 {ip}")
    if ficha:
        print(f"   nome: {ficha.get('friendlyName', '?')}")
        print(f"   fabricante: {ficha.get('manufacturer', '?')} | modelo: {ficha.get('modelName', '?')}")
    if servidor:
        print(f"   servidor: {servidor}")
    for p in portas:
        print(f"   porta {p} aberta → {PORTAS[p]}")
    print(f"   palpite: {palpite(portas, texto_total)}")


def main() -> None:
    if len(sys.argv) > 1:
        for ip in sys.argv[1:]:
            analisar_ip(ip, [])
        return
    print("A procurar dispositivos na rede (3 segundos)...")
    encontrados = ssdp_procurar()
    if not encontrados:
        print("Ninguém respondeu. Confirma que a TV está ligada e na mesma rede Wi-Fi.")
        print("Se souberes o IP da TV (Definições → Rede), corre: python3 descobrir_tv.py <IP>")
        return
    print(f"Encontrei {len(encontrados)} dispositivo(s). A analisar...")
    for ip, respostas in sorted(encontrados.items()):
        analisar_ip(ip, respostas)
    print("\nManda este resultado ao Claude 😉 (o router também aparece aqui, é normal).")


if __name__ == "__main__":
    main()
