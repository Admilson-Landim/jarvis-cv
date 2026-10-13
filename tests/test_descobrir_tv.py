import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import descobrir_tv as d  # noqa: E402

RESPOSTA = ("HTTP/1.1 200 OK\r\nLOCATION: http://192.168.88.50:7676/desc.xml\r\n"
            "SERVER: Linux/4.9 UPnP/1.0 AndroidTV\r\nST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n\r\n")


def test_cabecalho():
    assert d.cabecalho(RESPOSTA, "LOCATION") == "http://192.168.88.50:7676/desc.xml"
    assert "AndroidTV" in d.cabecalho(RESPOSTA, "server")


def test_palpites():
    assert d.palpite([6466], "").startswith("Android TV")
    assert d.palpite([], "Linux AndroidTV").startswith("Android TV")
    assert d.palpite([8002], "") == "Samsung Tizen"
    assert d.palpite([3000], "") == "LG webOS"
    assert d.palpite([36669], "") == "VIDAA / Hisense"
    assert d.palpite([8009], "").startswith("Tem Chromecast")
    assert d.palpite([7676], "").startswith("Só DLNA")
    assert d.palpite([], "") == "Desconhecido"


def test_portas_abertas_em_servidor_local():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen()
    porta = s.getsockname()[1]
    d.PORTAS[porta] = "teste"
    try:
        assert porta in d.portas_abertas("127.0.0.1")
    finally:
        del d.PORTAS[porta]
        s.close()
