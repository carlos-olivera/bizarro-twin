"""
Script utilitario para actualizar auth_token y ct0 en data/cookies/cookies.json.
Uso:
    python update_auth.py --auth_token NUEVO_TOKEN --ct0 NUEVO_CT0
"""

import argparse
import json
from pathlib import Path
import sys

COOKIES_PATH = Path("data/cookies/cookies.json")


def load_cookies():
    if not COOKIES_PATH.exists():
        return None
    try:
        return json.loads(COOKIES_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        sys.exit(f"❌ No se pudo leer {COOKIES_PATH}: {e}")


def save_cookies(data):
    try:
        COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
        COOKIES_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        sys.exit(f"❌ No se pudo escribir {COOKIES_PATH}: {e}")


def update_cookie_entries(data, auth_token, ct0):
    """
    Soporta dos formatos comunes:
    - Diccionario simple con llaves 'auth_token' y 'ct0'.
    - Lista de cookies estilo navegador: [{ "name": "auth_token", "value": "..."}, ...]
    """
    if isinstance(data, dict):
        data["auth_token"] = auth_token
        data["ct0"] = ct0
        return data

    if isinstance(data, list):
        def set_cookie(name, value):
            for cookie in data:
                if isinstance(cookie, dict) and cookie.get("name") == name:
                    cookie["value"] = value
                    return
            data.append({"name": name, "value": value})

        set_cookie("auth_token", auth_token)
        set_cookie("ct0", ct0)
        return data

    sys.exit("❌ Formato de cookies no soportado (se esperaba dict o lista).")


def main():
    parser = argparse.ArgumentParser(description="Actualiza auth_token y ct0 en cookies.json.")
    parser.add_argument("--auth_token", required=True, help="Valor de auth_token")
    parser.add_argument("--ct0", required=True, help="Valor de ct0")
    args = parser.parse_args()

    current = load_cookies()
    if current is None:
        # Si no existe, creamos un dict por defecto
        current = {}

    updated = update_cookie_entries(current, args.auth_token, args.ct0)
    save_cookies(updated)
    print(f"✅ cookies.json actualizado en {COOKIES_PATH}")


if __name__ == "__main__":
    main()
