#!/usr/bin/env python3
"""
Detetive de TVs: procura dispositivos na rede (SSDP/UPnP) e testa as portas
de controlo conhecidas, para sabermos como falar com a TV.

Uso (com a TV ligada e na mesma rede Wi-Fi do PC):
    python3 descobrir_tv.py                   # procura por UPnP e, se falhar, varre a rede
    python3 descobrir_tv.py --varrer          # varre todos os endereços da rede (~20 s)
    python3 descobrir_tv.py 192.168.88.50     # se já souberes o IP da TV
"""

import re
import socket
import subprocess
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


def meu_ip() -> str:
    """IP do PC na rede local (não envia nada, só pergunta ao sistema a rota)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def responde_ping(ip: str) -> bool:
    return subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def tabela_arp() -> dict:
    """{ip: mac} dos aparelhos que o PC viu na rede."""
    try:
        saida = subprocess.run(["ip", "neigh"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return {}
    macs = {}
    for linha in saida.splitlines():
        m = re.match(r"(\d+\.\d+\.\d+\.\d+) .*lladdr ([0-9a-f:]{17})", linha)
        if m:
            macs[m.group(1)] = m.group(2)
    return macs


def varrer_rede() -> None:
    eu = meu_ip()
    base = eu.rsplit(".", 1)[0]
    alvos = [f"{base}.{i}" for i in range(1, 255) if f"{base}.{i}" != eu]
    print(f"O teu PC é {eu}. A varrer {base}.1 a {base}.254 (uns 20 segundos)...")

    def sondar(ip):
        portas = portas_abertas(ip)
        if portas or responde_ping(ip):
            return ip, portas
        return None

    with ThreadPoolExecutor(max_workers=64) as ex:
        vivos = [r for r in ex.map(sondar, alvos) if r]
    macs = tabela_arp()
    if not vivos and not macs:
        print("Nenhum aparelho respondeu. O router pode estar a isolar os aparelhos Wi-Fi.")
        return
    # só a rede de casa (fora ficam, por exemplo, os contentores Docker 172.x)
    vistos = {ip for ip, _ in vivos} | {ip for ip in macs if ip.startswith(base + ".")}
    print(f"Encontrei {len(vistos)} aparelho(s):")
    for ip in sorted(vistos, key=lambda x: int(x.rsplit(".", 1)[1])):
        portas = dict(vivos).get(ip) or portas_abertas(ip)
        print(f"\n📍 {ip}   mac: {macs.get(ip, '?')}")
        for p in portas:
            print(f"   porta {p} aberta → {PORTAS[p]}")
        if portas:
            print(f"   palpite: {palpite(portas, '')}")
    print("\nDica: a TV costuma ser a que tem portas como 5555, 6466, 8008/8009 ou 7676.")
    print("Se nenhuma tiver portas, desliga a TV e corre outra vez: a que desaparecer é ela.")


def main() -> None:
    args = sys.argv[1:]
    if args == ["--varrer"]:
        varrer_rede()
        return
    if args:
        for ip in args:
            analisar_ip(ip, [])
        return
    print("A procurar dispositivos na rede (3 segundos)...")
    encontrados = ssdp_procurar()
    if not encontrados:
        print("Ninguém respondeu por UPnP. Vou varrer a rede endereço a endereço.\n")
        varrer_rede()
        return
    print(f"Encontrei {len(encontrados)} dispositivo(s). A analisar...")
    for ip, respostas in sorted(encontrados.items()):
        analisar_ip(ip, respostas)
    print("\nManda este resultado ao Claude 😉 (o router também aparece aqui, é normal).")


if __name__ == "__main__":
    main()
