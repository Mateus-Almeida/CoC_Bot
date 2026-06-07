import sys
import loguru
import warnings
import builtins
from datetime import datetime
from pathlib import Path

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

_original_print = builtins.print

# ============================================================
# 🖨️ Console Print Override (com timestamp e colorização)
# ============================================================

# Mensagens de baixo nível que devem ser filtradas do console
# quando DEBUG=False (ex: saídas internas de bibliotecas)
_NOISE_PATTERNS = [
    "locate confidence:",
    "libEGL",
    "libGL",
    "EGL_",
]

def custom_print(*args, **kwargs):
    # Permite \n isolado sem timestamp
    if len(args) == 1 and isinstance(args[0], str) and args[0] == "\n":
        _original_print(*args, **kwargs)
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    ts_formatted = f"\033[90m[{timestamp}]\033[0m"

    if args:
        first_arg = args[0]
        if isinstance(first_arg, str):
            # Passa direto strings que já têm escape de cor ou são de lib
            if first_arg.startswith("\033") or (first_arg.startswith("[") and not first_arg.startswith("[1") and not first_arg.startswith("[0")):
                _original_print(*args, **kwargs)
                return

            # Filtra mensagens de ruído de baixo nível
            first_lower = first_arg.lower()
            for noise in _NOISE_PATTERNS:
                if noise.lower() in first_lower:
                    # Ainda registra no log de arquivo, mas não exibe no console
                    loguru.logger.debug(first_arg)
                    return

            text_lower = first_lower
            color_prefix = ""
            color_suffix = "\033[0m"

            if "---" in text_lower or "ciclo" in text_lower or "reiniciando" in text_lower:
                color_prefix = "\033[95m\033[1m"  # Magenta Bold
            elif any(k in text_lower for k in ["erro", "falhou", "failed", "error", "exception", "crítico", "critico"]):
                color_prefix = "\033[91m"  # Vermelho
            elif any(k in text_lower for k in ["⚠️", "aviso", "warning", "limite", "slash", "not found", "não encontrado"]):
                color_prefix = "\033[93m"  # Amarelo
            elif any(k in text_lower for k in ["✅", "sucesso", "concluído", "concluida", "carregada", "connected", "iniciado", "batalha iniciada"]):
                color_prefix = "\033[92m"  # Verde
            elif any(k in text_lower for k in ["⚔️", "🔍", "📋", "🗺️", "iniciando", "buscando", "carregando", "lançando", "preparando", "aguardando", "deployando", "deploy"]):
                color_prefix = "\033[96m"  # Ciano
            elif any(k in text_lower for k in ["ℹ️", "→", "slot", "itera"]):
                color_prefix = "\033[37m"  # Branco apagado

            formatted_first = f"{color_prefix}{first_arg}{color_suffix}" if color_prefix else first_arg
            _original_print(f"{ts_formatted} {formatted_first}", *args[1:], **kwargs)
        else:
            _original_print(f"{ts_formatted} {first_arg}", *args[1:], **kwargs)
    else:
        _original_print(ts_formatted, **kwargs)


builtins.print = custom_print


# ============================================================
# 📂 Streams auxiliares para loguru
# ============================================================

class Logger:
    """Redireciona writes para loguru (usado quando frozen)."""
    def __init__(self, level):
        self.level = level

    def write(self, data):
        data = data.strip()
        if data:
            loguru.logger.log(self.level, data)

    def flush(self):
        pass


class Tee:
    """Escreve em múltiplos streams simultaneamente."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass


# ============================================================
# 🗂️ Inicialização de logs em arquivo
# ============================================================

def _get_log_dir():
    """Resolve o diretório de logs de forma unificada."""
    import configs
    if getattr(sys, "frozen", False):
        base = Path.home() / ".CoC_Bot"
        base.mkdir(exist_ok=True)
        return base / getattr(configs, "LOG_DIR", "logs")
    else:
        return Path(__file__).parent / getattr(configs, "LOG_DIR", "logs")


def _rotate_old_logs(log_dir: Path, max_files: int):
    """Remove os arquivos de log mais antigos quando o limite é atingido."""
    logs = sorted(log_dir.glob("session_*.log"), key=lambda p: p.stat().st_mtime)
    while len(logs) >= max_files:
        try:
            logs.pop(0).unlink()
        except Exception:
            break


def enable_logging(id: str):
    """
    Ativa o sistema de logging em arquivo.

    Cria (se necessário) a pasta LOG_DIR e um arquivo de sessão com
    timestamp, mantendo no máximo MAX_LOG_FILES arquivos.
    """
    import configs

    log_dir = _get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    max_files = getattr(configs, "MAX_LOG_FILES", 10)
    _rotate_old_logs(log_dir, max_files)

    session_ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_dir / f"session_{session_ts}_{id}.log"

    exclude_modules = ["pyminitouch"]

    loguru.logger.add(
        log_path,
        rotation="10 MB",
        retention=max_files,
        compression="zip",
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        filter=lambda record: not any(record["name"].startswith(mod) for mod in exclude_modules),
    )

    _original_print(f"\033[90m[log]\033[0m Sessão iniciada → {log_path}")

    if getattr(sys, "frozen", False):
        sys.stdout = Logger("INFO")
        sys.stderr = Logger("ERROR")
    else:
        sys.stdout = Tee(sys.__stdout__, Logger("INFO"))
        sys.stderr = Tee(sys.__stderr__, Logger("ERROR"))

    return log_path


def write_session_report(report_text: str):
    """Grava o relatório final de sessão diretamente via loguru (ignora stdout Tee)."""
    loguru.logger.info(report_text)
