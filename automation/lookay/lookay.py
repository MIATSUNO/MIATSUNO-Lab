#!/usr/bin/env python3
import argparse
import ast
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

API_ROOT = "https://kaystant-api.onrender.com"
SITE_ROOT = "https://kayepad.neocities.org"
VERISTANTE_URL = SITE_ROOT + "/site/veristante"
APP_URL = SITE_ROOT + "/site/main"
MAX_API_BYTES = 2 * 1024 * 1024
MAX_PAGE_BYTES = 5 * 1024 * 1024
MAX_BOOK_BYTES = 12 * 1024 * 1024
CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
CONFIG_DIR = CONFIG_HOME / "lookay"
SESSION_FILE = CONFIG_DIR / "session.json"
STATE_FILE = CONFIG_DIR / "site_watch_state.json"


class LookayError(Exception):
    pass


class ApiError(LookayError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def now_ms():
    return int(time.time() * 1000)


def request_bytes(url, method="GET", payload=None, token=None, limit=MAX_API_BYTES, browser_headers=False):
    headers = {
        "User-Agent": "LOOKAY/1.0 (Termux; Kayepad-compatible client)",
        "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    }
    if browser_headers:
        headers["Origin"] = SITE_ROOT
        headers["Referer"] = APP_URL
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=25) as response:
            body = response.read(limit + 1)
            if len(body) > limit:
                raise LookayError("A resposta passou do limite de segurança configurado.")
            return body, response.geturl(), response.headers
    except HTTPError as exc:
        body = exc.read(min(limit, 8192))
        detail = ""
        try:
            parsed = json.loads(body.decode("utf-8", "replace"))
            value = parsed.get("detail") or parsed.get("message") or parsed.get("error") or ""
            if isinstance(value, list):
                detail = " ".join(str(item.get("msg") or item) for item in value)
            else:
                detail = str(value)
        except (ValueError, AttributeError):
            pass
        message = detail or f"A Kayepad respondeu com HTTP {exc.code}."
        raise ApiError(message, exc.code) from None
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise LookayError(f"Não consegui acessar o serviço: {exc}") from None


def api_json(path, method="GET", payload=None, token=None):
    body, _, _ = request_bytes(API_ROOT + path, method, payload, token, MAX_API_BYTES, True)
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise LookayError("A resposta do serviço não veio em JSON válido.") from None
    if not isinstance(value, dict):
        raise LookayError("A resposta do serviço veio em formato inesperado.")
    return value


def get_session():
    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise LookayError("Você ainda não entrou. Use: lookay login") from None
    except (OSError, ValueError):
        raise LookayError("O arquivo de sessão local não pôde ser lido; entre novamente com lookay login.") from None
    token = data.get("token") if isinstance(data, dict) else None
    if not isinstance(token, str) or len(token) < 16:
        raise LookayError("A sessão local está inválida; entre novamente com lookay login.")
    return data


def save_session(token, user):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(CONFIG_DIR, 0o700)
    except OSError:
        pass
    record = {
        "token": token,
        "username": str(user.get("username") or ""),
        "display_name": str(user.get("display_name") or user.get("name") or ""),
        "saved_at": now_iso(),
    }
    fd = os.open(SESSION_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False)
        handle.write("\n")
    try:
        os.chmod(SESSION_FILE, 0o600)
    except OSError:
        pass


def unwrap_user(data):
    user = data.get("user", data) if isinstance(data, dict) else {}
    return user if isinstance(user, dict) else {}


def command_login(_args):
    email = input("Email da Kayepad: ").strip()
    if not email:
        raise LookayError("Digite o email da sua conta.")
    import getpass
    password = getpass.getpass("Senha (não aparece na tela): ")
    if not password:
        raise LookayError("A senha não pode ficar vazia.")
    data = api_json("/auth/login", "POST", {"email": email, "password": password})
    token = data.get("token")
    if not isinstance(token, str) or len(token) < 16:
        raise LookayError("A Kayepad não retornou uma sessão válida.")
    user = unwrap_user(data)
    save_session(token, user)
    identity = user.get("display_name") or user.get("name") or user.get("username") or email
    print(f"Entrada concluída como {identity}.")
    print(f"A sessão fica só no seu Termux, em {SESSION_FILE}, protegida pelas permissões locais do arquivo.")
    print("Sua senha não é salva. Use lookay logout para encerrar e apagar a sessão local.")


def command_status(_args):
    session = get_session()
    try:
        data = api_json("/me", token=session["token"])
    except ApiError as exc:
        if exc.status == 401:
            raise LookayError("A sessão expirou. Use: lookay login") from None
        raise
    user = unwrap_user(data)
    identity = user.get("display_name") or user.get("name") or user.get("username") or session.get("username") or "conta Kayepad"
    print(f"Conectado como {identity}.")


def command_logout(_args):
    session = get_session()
    try:
        api_json("/auth/logout", "POST", {}, session["token"])
    except ApiError as exc:
        if exc.status not in (401, 404):
            raise
    try:
        SESSION_FILE.unlink()
    except FileNotFoundError:
        pass
    print("Sessão encerrada e removida deste Termux.")


def extract_js_object(source, start):
    opening = source.find("{", start)
    if opening < 0:
        return None
    depth = 0
    quote = None
    escaped = False
    for index in range(opening, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[opening:index + 1]
    return None


def js_string_field(obj, key):
    pattern = r"(?:^|[,{])\s*" + re.escape(key) + r"\s*:\s*(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"
    match = re.search(pattern, obj, re.S)
    if not match:
        return ""
    try:
        value = ast.literal_eval(match.group(1))
    except (SyntaxError, ValueError):
        return ""
    return value if isinstance(value, str) else ""


def parse_catalog(source):
    works = []
    for match in re.finditer(r"\bFIRST_BOOK\s*=\s*\{", source):
        obj = extract_js_object(source, match.start())
        if not obj:
            continue
        work = {
            "id": js_string_field(obj, "id"),
            "title": js_string_field(obj, "title"),
            "author": js_string_field(obj, "author"),
            "synopsis": js_string_field(obj, "synopsis"),
        }
        if work["title"] and work["author"] and work["synopsis"]:
            if not any(item["id"] == work["id"] and item["title"] == work["title"] for item in works):
                works.append(work)
    return works


def command_obras(args):
    body, _, _ = request_bytes(VERISTANTE_URL, limit=MAX_PAGE_BYTES)
    page = body.decode("utf-8", "replace")
    works = parse_catalog(page)
    if args.search:
        query = args.search.casefold()
        works = [work for work in works if query in work["title"].casefold() or query in work["author"].casefold() or query in work["synopsis"].casefold()]
    if args.json:
        print(json.dumps(works, ensure_ascii=False, indent=2))
        return
    if not works:
        print("Não encontrei obras no formato atual do catálogo.")
        print("Veristante:", VERISTANTE_URL)
        return
    for index, work in enumerate(works, 1):
        print(f"{index}. {work['title']}\n   Autoria: {work['author']}\n   Sinopse: {work['synopsis']}\n")


def safe_filename(value):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_value).strip("._-")
    return (cleaned[:100] or "obra") + ".json"


def count_words(text):
    return len(re.findall(r"\S+", text.strip(), re.UNICODE)) if text.strip() else 0


def editor_text(label):
    editor = os.environ.get("EDITOR", "").strip()
    if editor and shutil.which(shlex.split(editor)[0]):
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".txt", delete=False) as handle:
            path = Path(handle.name)
        try:
            print(f"Abrindo o editor para {label}. Salve e feche para continuar.")
            subprocess.run(shlex.split(editor) + [str(path)], check=True)
            return path.read_text(encoding="utf-8")
        finally:
            try:
                path.unlink()
            except OSError:
                pass
    print(f"{label} — digite o texto; uma linha contendo apenas . encerra:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == ".":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def prompt_required(label, default=None):
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    value = value or (default or "")
    if not value:
        raise LookayError(f"{label} não pode ficar vazio.")
    return value


def prompt_optional(label):
    return input(f"{label} (opcional): ").strip()


def command_escrever(args):
    session = get_session()
    user = unwrap_user(api_json("/me", token=session["token"]))
    default_author = user.get("display_name") or user.get("name") or user.get("username") or session.get("username") or ""
    title = prompt_required("Título da obra")
    author = prompt_required("Nome ou pseudônimo do autor", default_author)
    synopsis = prompt_optional("Sinopse")[:1200]
    cover_url = prompt_optional("URL da capa")[:1000]
    if cover_url:
        parts = urlsplit(cover_url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
            raise LookayError("A capa precisa usar um endereço http ou https válido.")
    chapters = []
    while True:
        chapter_title = input(f"Título do capítulo {len(chapters) + 1} (vazio para terminar): ").strip()
        if not chapter_title:
            if chapters:
                break
            raise LookayError("A obra precisa ter pelo menos um capítulo.")
        content = editor_text(f"capítulo {len(chapters) + 1}")
        chapters.append({
            "id": "chap_" + uuid.uuid4().hex,
            "title": chapter_title,
            "content": content,
            "wordCount": count_words(content),
            "updatedAt": now_ms(),
            "history": [],
        })
    book = {
        "type": "BOOK",
        "title": title[:300],
        "author": author[:200],
        "synopsis": synopsis,
        "coverUrl": cover_url,
        "chapters": chapters,
    }
    encoded = (json.dumps(book, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAX_BOOK_BYTES:
        raise LookayError("O JSON passou de 12 MB, limite aceito pela importação da Kayepad.")
    output = Path(args.output).expanduser() if args.output else Path(safe_filename(title))
    if output.exists():
        raise LookayError(f"O arquivo já existe: {output}. Escolha outro caminho com --output.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    print(f"JSON da obra salvo em: {output.resolve()}")
    print("Na Kayepad, abra Vias › Adicionar uma obra e selecione esse arquivo.")


def canonical_url(value):
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError(f"Endereço inválido: {value}")
    host = parts.hostname.lower()
    if parts.port is not None:
        host = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme.lower(), host, parts.path or "/", parts.query, ""))


def read_urls(args):
    values = list(args.urls)
    if args.url_file:
        try:
            values.extend(line.strip() for line in Path(args.url_file).expanduser().read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#"))
        except OSError as exc:
            raise LookayError(f"Não consegui ler o arquivo de URLs: {exc}") from None
    unique = []
    seen = set()
    for value in values:
        url = canonical_url(value)
        if url not in seen:
            unique.append(url)
            seen.add(url)
    if not unique:
        raise LookayError("Informe pelo menos uma página ou um arquivo com URLs.")
    return unique


def parse_headers(values):
    headers = {}
    forbidden = {"host", "content-length", "connection", "transfer-encoding"}
    for value in values:
        if ":" not in value:
            raise LookayError("Cabeçalho adicional precisa usar NOME:VALOR.")
        name, content = value.split(":", 1)
        name = name.strip()
        content = content.strip()
        if not name or not content or name.lower() in forbidden:
            raise LookayError(f"Cabeçalho inválido: {name or value}")
        headers[name] = content
    return headers


def load_watch_state(path):
    if not path.exists():
        return {"version": 1, "sites": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise LookayError(f"Não consegui ler o estado do monitor: {path}") from None
    if not isinstance(data, dict) or not isinstance(data.get("sites"), dict):
        raise LookayError("O arquivo de estado do monitor tem um formato inválido.")
    data.setdefault("version", 1)
    return data


def save_watch_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def watch_one(url, previous, args, extra_headers):
    headers = {"User-Agent": args.user_agent, "Accept": "*/*"}
    headers.update(extra_headers)
    if previous and previous.get("etag"):
        headers["If-None-Match"] = str(previous["etag"])
    if previous and previous.get("last_modified"):
        headers["If-Modified-Since"] = str(previous["last_modified"])
    request = Request(url, headers=headers, method="GET")
    checked = now_iso()
    try:
        with urlopen(request, timeout=args.timeout) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > args.max_bytes:
                raise LookayError(f"A resposta de {url} passou do limite de {args.max_bytes} bytes.")
            body = response.read(args.max_bytes + 1)
            if len(body) > args.max_bytes:
                raise LookayError(f"A resposta de {url} passou do limite de {args.max_bytes} bytes.")
            current = {
                "url": url,
                "status_code": int(response.status),
                "final_url": canonical_url(response.geturl()),
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "checked_at": checked,
                "error": None,
            }
    except HTTPError as exc:
        if exc.code == 304 and previous:
            current = dict(previous)
            current["checked_at"] = checked
            current["status_code"] = 304
            current["error"] = None
            return {"url": url, "result": "unchanged", "status_code": 304, "state": current}
        return {"url": url, "status": "error", "status_code": exc.code, "checked_at": checked, "error": f"HTTP {exc.code}: {exc.reason}"}
    except (URLError, TimeoutError, OSError, ValueError, LookayError) as exc:
        return {"url": url, "status": "error", "checked_at": checked, "error": str(exc)}
    if not previous:
        result = "new"
    elif any(current.get(key) != previous.get(key) for key in ("sha256", "status_code", "final_url")):
        result = "changed"
    else:
        result = "unchanged"
    return {"url": url, "result": result, "status_code": current["status_code"], "state": current}


def command_acompanhar(args):
    urls = read_urls(args)
    headers = parse_headers(args.header)
    state_path = Path(args.state).expanduser() if args.state else STATE_FILE
    state = load_watch_state(state_path)
    changed_seen = False
    error_seen = False
    while True:
        results = []
        for url in urls:
            previous = state["sites"].get(url)
            result = watch_one(url, previous, args, headers)
            if result.get("result"):
                state["sites"][url] = result["state"]
                changed_seen = changed_seen or result["result"] in {"new", "changed"}
            else:
                error_seen = True
                retained = dict(previous or {})
                retained.update({"url": url, "checked_at": result["checked_at"], "error": result["error"]})
                if result.get("status_code") is not None:
                    retained["status_code"] = result["status_code"]
                state["sites"][url] = retained
            results.append({key: value for key, value in result.items() if key != "state"})
        state["updated_at"] = now_iso()
        save_watch_state(state_path, state)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for result in results:
                if result.get("result"):
                    print(f"{result['result'].upper():9} {result.get('status_code', '?')!s:4} {result['url']}")
                else:
                    print(f"ERRO      {result.get('status_code', '—')!s:4} {result['url']}: {result['error']}", file=sys.stderr)
        if args.interval <= 0:
            break
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("Acompanhamento encerrado.", file=sys.stderr)
            break
    if error_seen:
        return 1
    if args.fail_on_change and changed_seen:
        return 3
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="lookay", description="Leia a Veristante, crie JSONs para a Kayepad e acompanhe páginas no Termux.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("login", help="entrar na conta Kayepad pelo Termux").set_defaults(func=command_login)
    commands.add_parser("logout", help="encerrar e apagar a sessão local").set_defaults(func=command_logout)
    commands.add_parser("status", help="confirmar a sessão Kayepad").set_defaults(func=command_status)
    obras = commands.add_parser("obras", help="ler títulos, autoria e sinopses da Veristante")
    obras.add_argument("--search", help="filtrar por título, autor ou sinopse")
    obras.add_argument("--json", action="store_true", help="mostrar os resultados em JSON")
    obras.set_defaults(func=command_obras)
    escrever = commands.add_parser("escrever", help="criar uma obra e exportar JSON para importar na Kayepad")
    escrever.add_argument("-o", "--output", help="caminho do JSON de saída")
    escrever.set_defaults(func=command_escrever)
    acompanhar = commands.add_parser("acompanhar", help="monitorar mudanças em páginas HTTP(S)")
    acompanhar.add_argument("urls", nargs="*", help="páginas para acompanhar")
    acompanhar.add_argument("-f", "--url-file", help="arquivo com uma URL por linha")
    acompanhar.add_argument("-s", "--state", help="arquivo JSON para guardar os resultados")
    acompanhar.add_argument("-i", "--interval", type=float, default=0, help="intervalo em segundos; repete até Ctrl-C se maior que zero")
    acompanhar.add_argument("-t", "--timeout", type=float, default=20, help="tempo máximo por página em segundos")
    acompanhar.add_argument("--max-bytes", type=int, default=5 * 1024 * 1024, help="tamanho máximo da resposta por página")
    acompanhar.add_argument("--user-agent", default="LOOKAY-site-watch/1.0", help="identificação enviada ao site")
    acompanhar.add_argument("--header", action="append", default=[], help="cabeçalho extra NOME:VALOR; não salve valores privados em arquivos públicos")
    acompanhar.add_argument("--json", action="store_true", help="mostrar resultados em JSON")
    acompanhar.add_argument("--fail-on-change", action="store_true", help="usar código de saída 3 se uma página mudar")
    acompanhar.set_defaults(func=command_acompanhar)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "acompanhar" and (args.interval < 0 or args.timeout <= 0 or args.max_bytes <= 0):
        parser.error("--interval não pode ser negativo; --timeout e --max-bytes precisam ser positivos")
    try:
        result = args.func(args)
        return result if isinstance(result, int) else 0
    except (LookayError, ApiError) as exc:
        print(f"LOOKAY: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrompido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
