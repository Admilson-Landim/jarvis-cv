"""
Tempo (meteorologia) com o Open-Meteo: gratuito e sem chave.

Teste isolado:
    python3 tempo.py
"""

import json
import urllib.parse
import urllib.request

from config import CIDADE, LATITUDE, LONGITUDE, FUSO_HORARIO

# Códigos WMO usados pelo Open-Meteo
DESCRICOES = {
    0: "céu limpo", 1: "quase limpo", 2: "parcialmente nublado", 3: "nublado",
    45: "nevoeiro", 48: "nevoeiro", 51: "chuvisco fraco", 53: "chuvisco", 55: "chuvisco forte",
    61: "chuva fraca", 63: "chuva", 65: "chuva forte", 80: "aguaceiros fracos",
    81: "aguaceiros", 82: "aguaceiros fortes", 95: "trovoada", 96: "trovoada com granizo",
    99: "trovoada com granizo",
}


def descrever(codigo) -> str:
    return DESCRICOES.get(int(codigo), "tempo variável") if codigo is not None else "tempo desconhecido"


def obter() -> dict | None:
    """Devolve o tempo atual e de hoje, ou None se não houver internet."""
    params = urllib.parse.urlencode({
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": FUSO_HORARIO,
        "forecast_days": 1,
    })
    try:
        with urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{params}", timeout=8) as r:
            dados = json.loads(r.read())
        atual, dia = dados["current"], dados["daily"]
        return {
            "cidade": CIDADE,
            "agora": round(atual["temperature_2m"]),
            "sensacao": round(atual["apparent_temperature"]),
            "ceu": descrever(atual.get("weather_code")),
            "vento": round(atual["wind_speed_10m"]),
            "maxima": round(dia["temperature_2m_max"][0]),
            "minima": round(dia["temperature_2m_min"][0]),
            "chuva": dia.get("precipitation_probability_max", [None])[0],
        }
    except Exception as erro:
        print(f"  (não consegui obter o tempo: {erro})")
        return None


def frase(t: dict) -> str:
    texto = (f"Na {t['cidade']} estão {t['agora']} graus, com {t['ceu']}. "
             f"Hoje a máxima é de {t['maxima']} e a mínima de {t['minima']}.")
    if t.get("chuva") is not None and t["chuva"] >= 30:
        texto += f" Há {t['chuva']} por cento de probabilidade de chuva."
    return texto


if __name__ == "__main__":
    t = obter()
    print(t)
    if t:
        print(frase(t))
