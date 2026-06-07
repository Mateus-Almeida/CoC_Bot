import sys
import loguru
import warnings
import builtins
from datetime import datetime
from pathlib import Path

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

_original_print = builtins.print

def custom_print(*args, **kwargs):
    if len(args) == 1 and isinstance(args[0], str) and args[0] == "\n":
        _original_print(*args, **kwargs)
        return
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    ts_formatted = f"\033[90m[{timestamp}]\033[0m"
    
    if args:
        first_arg = args[0]
        if isinstance(first_arg, str):
            if first_arg.startswith("\033") or (first_arg.startswith("[") and not first_arg.startswith("[12:")):
                _original_print(*args, **kwargs)
                return
            
            text_lower = first_arg.lower()
            color_prefix = ""
            color_suffix = "\033[0m"
            
            if "---" in text_lower or "ciclo" in text_lower or "reiniciando" in text_lower:
                color_prefix = "\033[95m\033[1m" # Magenta Bold
            elif "erro" in text_lower or "falhou" in text_lower or "failed" in text_lower or "error" in text_lower or "exception" in text_lower:
                color_prefix = "\033[91m" # Vermelho
            elif "sucesso" in text_lower or "concluído" in text_lower or "concluida" in text_lower or "carregada" in text_lower or "connected" in text_lower or "limpa" in text_lower or "limpeza" in text_lower or "batalha iniciada" in text_lower:
                color_prefix = "\033[92m" # Verde
            elif "iniciando" in text_lower or "buscando" in text_lower or "carregando" in text_lower or "lançando" in text_lower or "preparando" in text_lower or "aguardando" in text_lower:
                color_prefix = "\033[96m" # Ciano
            elif "not found" in text_lower or "aviso" in text_lower or "warning" in text_lower or "limite" in text_lower or "slash" in text_lower:
                color_prefix = "\033[93m" # Amarelo
                
            if color_prefix:
                formatted_first = f"{color_prefix}{first_arg}{color_suffix}"
            else:
                formatted_first = first_arg
                
            _original_print(f"{ts_formatted} {formatted_first}", *args[1:], **kwargs)
        else:
            _original_print(f"{ts_formatted} {first_arg}", *args[1:], **kwargs)
    else:
        _original_print(ts_formatted, **kwargs)

builtins.print = custom_print

class Logger:
    def __init__(self, level):
        self.level = level

    def write(self, data):
        data = data.strip()
        if data:
            loguru.logger.log(self.level, data)

    def flush(self):
        pass

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except:
                pass

def enable_logging(id):
    if getattr(sys, "frozen", False):
        APP_DATA_DIR = Path.home() / ".CoC_Bot"
        APP_DATA_DIR.mkdir(exist_ok=True)
        LOG_DIR = APP_DATA_DIR / "debug"
    else:
        LOG_DIR = Path("debug")

    LOG_DIR.mkdir(exist_ok=True)

    LOG_PATH = LOG_DIR / f"{id}.log"

    exclude_modules = [
        "pyminitouch",
    ]

    loguru.logger.add(
        LOG_PATH,
        rotation="10 MB",
        retention=5,
        compression="zip",
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        filter=lambda record: not any(record["name"].startswith(mod) for mod in exclude_modules),
    )

    if getattr(sys, "frozen", False):
        sys.stdout = Logger("INFO")
        sys.stderr = Logger("ERROR")
    else:
        sys.stdout = Tee(sys.__stdout__, Logger("INFO"))
        sys.stderr = Tee(sys.__stderr__, Logger("ERROR"))
