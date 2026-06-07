import utils
from utils import *
from configs import *
from upgrader import Upgrader
from attacker import Attacker
import random
import time
from datetime import datetime

# ============================================================
# 📊 Attack Session — Registro Individual de Ataques
# ============================================================

class AttackRecord:
    """Registra os dados de um único ataque."""

    def __init__(self, attack_type: str, attack_number: int):
        self.attack_number = attack_number
        self.attack_type = attack_type          # "home_base" | "builder_base"
        self.started_at = datetime.now()
        self.finished_at: datetime | None = None
        self.success: bool | None = None
        self.failure_reason: str = ""

    def finish(self, success: bool, failure_reason: str = ""):
        self.finished_at = datetime.now()
        self.success = success
        self.failure_reason = failure_reason

    @property
    def duration_str(self) -> str:
        if self.finished_at is None:
            return "?"
        delta = int((self.finished_at - self.started_at).total_seconds())
        m, s = divmod(delta, 60)
        return f"{m}m{s:02d}s"

    @property
    def started_at_str(self) -> str:
        return self.started_at.strftime("%H:%M:%S")

    @property
    def type_label(self) -> str:
        return "🏠 Home Base" if self.attack_type == "home_base" else "🔨 Builder Base"


class AttackSession:
    """
    Gerencia o registro e relatório de todos os ataques da sessão atual.
    Armazena cada AttackRecord e gera relatório formatado ao final.
    """

    def __init__(self):
        self.session_start = datetime.now()
        self.records: list[AttackRecord] = []

    def start_attack(self, attack_type: str) -> AttackRecord:
        n = len(self.records) + 1
        record = AttackRecord(attack_type, n)
        self.records.append(record)
        print(f"\n⚔️  [Ataque #{n}] {record.type_label} — iniciado às {record.started_at_str}")
        return record

    def finish_attack(self, record: AttackRecord, success: bool, failure_reason: str = ""):
        record.finish(success, failure_reason)
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"   {status} — duração: {record.duration_str}" + (f" | motivo: {failure_reason}" if not success else ""))

    def summary(self) -> dict:
        total = len(self.records)
        successes = sum(1 for r in self.records if r.success)
        failures = total - successes
        rate = (successes / total * 100) if total > 0 else 0.0
        return {"total": total, "successes": successes, "failures": failures, "rate": rate}

    def format_report(self) -> str:
        s = self.summary()
        now = datetime.now()
        elapsed = now - self.session_start
        h, rem = divmod(int(elapsed.total_seconds()), 3600)
        m, sec = divmod(rem, 60)
        elapsed_str = f"{h}h {m}min {sec}s" if h else f"{m}min {sec}s"

        lines = [
            "",
            "╔══════════════════════════════════════════════════════════╗",
            "║                 📊 RELATÓRIO DA SESSÃO                   ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║  Início da sessão : {self.session_start.strftime('%d/%m/%Y %H:%M:%S'):<35}║",
            f"║  Encerramento     : {now.strftime('%d/%m/%Y %H:%M:%S'):<35}║",
            f"║  Duração total    : {elapsed_str:<35}║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║  Total de ataques : {s['total']:<35}║",
            f"║  ✅ Sucessos      : {s['successes']:<35}║",
            f"║  ❌ Falhas        : {s['failures']:<35}║",
        ]
        rate_str = f"{s['rate']:.1f}%"
        lines.append(f"║  Taxa de sucesso  : {rate_str:<35}║")

        failed = [r for r in self.records if not r.success]
        if failed:
            lines += [
                "╠══════════════════════════════════════════════════════════╣",
                "║  🔎 DETALHES DAS FALHAS:                                 ║",
            ]
            for r in failed:
                reason = r.failure_reason or "motivo não registrado"
                header = f"  #{r.attack_number} — {r.started_at_str} — {r.type_label}"
                detail = f"      Motivo: {reason}"
                lines.append(f"║  {header:<54}║")
                lines.append(f"║  {detail:<54}║")

        lines += [
            "╚══════════════════════════════════════════════════════════╝",
            "",
        ]
        return "\n".join(lines)

    def print_report(self):
        """Exibe o relatório no console e grava no log."""
        from log import write_session_report
        report = self.format_report()
        # Usa _original_print para não duplicar o timestamp do custom_print
        import builtins
        # O custom_print vai adicionar timestamp, o que distorce o relatório
        # Acessamos o print original para exibir o bloco sem prefixo
        try:
            from log import _original_print as raw_print
        except ImportError:
            raw_print = builtins.print
        raw_print(report)
        try:
            write_session_report(report)
        except Exception:
            pass


# ============================================================
# 🤖 CoC_Bot — Controlador principal
# ============================================================

class CoC_Bot:
    def __init__(self):
        self.cycle_count = 0
        self.total_attacks = 0
        self.successful_attacks = 0
        self.failed_attacks = 0
        self.quick_retry = False
        self.session = AttackSession()
        pre_init_ocr()
        self.start_bluestacks()
        self.connect_adb()
        self.upgrader = Upgrader()
        self.attacker = Attacker()
        print(f"🤖 CoC Bot inicializado. Sessão iniciada às {self.session.session_start.strftime('%H:%M:%S')}")

    # ============================================================
    # 🖥️ System & Emulator Management
    # ============================================================

    def update_status(self, status):
        import requests

        if WEB_APP_URL != "":
            try:
                requests.post(
                    f"{WEB_APP_URL}/{utils.INSTANCE_ID}/status",
                    json={"status": status},
                    timeout=(1, 2)
                )
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("update_status", e)
        if utils.CACHE.get("gui_port") is not None:
            try:
                requests.post(
                    f"http://localhost:{utils.CACHE['gui_port']}/status",
                    json={"status": status},
                    timeout=(1, 2)
                )
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("update_status", e)

    def start_bluestacks(self):
        import sys, subprocess

        if self.check_bluestacks():
            if configs.DEBUG: print("BlueStacks já está em execução.")
            return

        if sys.platform == "darwin":
            subprocess.Popen(
                ["osascript", "-e",
                 'tell application "BlueStacks" to launch\n'
                 'tell application "BlueStacks" to set visible of front window to false'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        elif sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 6
            subprocess.Popen(
                [r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                startupinfo=startupinfo
            )

        for _ in range(120):
            if self.check_bluestacks():
                if configs.DEBUG: print("BlueStacks iniciado com sucesso.")
                return
            time.sleep(0.5)

        raise Exception("BlueStacks falhou ao iniciar.")

    def check_bluestacks(self):
        import psutil, sys
        for proc in psutil.process_iter(['name']):
            if proc.info['name']:
                name = proc.info['name'].lower()
                if sys.platform == "win32":
                    if 'hd-player.exe' in name:
                        return True
                else:
                    if 'bluestacks' in name or 'hd-player' in name:
                        return True
        return False

    def connect_adb(self):
        for attempt in range(30):
            try:
                connect_adb()
                if configs.DEBUG: print("ADB conectado com sucesso.")
                return
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print(f"connect_adb (tentativa {attempt + 1}/30): {e}")
            time.sleep(2.0)
        raise Exception("Falha ao conectar ao ADB.")

    def restart_bluestacks_flow(self):
        import subprocess, sys

        print("\n=== Reiniciando o BlueStacks preventivamente para liberar memória RAM ===")
        self.update_status("restarting")

        try:
            stop_coc()
        except Exception:
            pass

        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "HD-Player.exe"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == "darwin":
            subprocess.run(["osascript", "-e", 'quit application "BlueStacks"'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("Aguardando 5 segundos para liberação dos recursos no sistema operacional...")
        time.sleep(5)

        self.start_bluestacks()
        self.connect_adb()
        print("=== BlueStacks reiniciado e ADB reconectado com sucesso ===\n")

    # ============================================================
    # ⚔️ Attack helpers com registro de sessão
    # ============================================================

    def _run_home_attack(self, restart: bool) -> bool:
        """Executa ataque na Vila Principal e registra o resultado na sessão."""
        record = self.session.start_attack("home_base")
        success = self.attacker.run_home_base(restart=restart)
        reason = "" if success else "Oponente não encontrado, timeout ou falha no deploy de tropas"
        self.session.finish_attack(record, success, reason)
        return success

    def _run_builder_attack(self, restart: bool = True) -> bool:
        """Executa ataque na Vila do Construtor e registra o resultado na sessão."""
        record = self.session.start_attack("builder_base")
        success = self.attacker.run_builder_base(restart=restart)
        reason = "" if success else "Oponente não encontrado ou timeout no matchmaking"
        self.session.finish_attack(record, success, reason)
        return success

    # ============================================================
    # ⏱️ Main Loop
    # ============================================================

    def run(self):
        import gc

        print("--- Iniciando loop principal do CoC Bot ---")

        try:
            while True:
                try:
                    gc.collect()

                    if not running():
                        time.sleep(1)
                        continue

                    print("--- Iniciando um novo ciclo de verificação ---")
                    cycle_success = True
                    if start_coc():
                        self.update_status("now")

                        Task_Handler.get_exclusions()
                        exclude_home_base = Task_Handler.home_base_excluded(use_cached=True)
                        exclude_home_lab = Task_Handler.home_lab_excluded(use_cached=True)
                        skip_home_base_upgrades = exclude_home_base and exclude_home_lab
                        exclude_home_attacks = Task_Handler.home_attacks_excluded(use_cached=True)

                        exclude_builder_base = Task_Handler.builder_base_excluded(use_cached=True)
                        exclude_builder_lab = Task_Handler.builder_lab_excluded(use_cached=True)
                        skip_builder_base_upgrades = exclude_builder_base and exclude_builder_lab
                        exclude_builder_attacks = Task_Handler.builder_attacks_excluded(use_cached=True)

                        # ── Vila Principal ──────────────────────────────
                        if not skip_home_base_upgrades or not exclude_home_attacks:
                            to_home_base(ref_cache=True)

                        if not skip_home_base_upgrades:
                            self.upgrader.run_home_base(exclude_home_base, exclude_home_lab)

                        if not exclude_home_attacks:
                            should_restart = not skip_home_base_upgrades or not skip_builder_base_upgrades
                            success = self._run_home_attack(restart=should_restart)
                            if success:
                                self.successful_attacks += 1
                            else:
                                self.failed_attacks += 1
                                cycle_success = False
                            self.total_attacks += 1

                        # ── Vila do Construtor ──────────────────────────
                        if not skip_builder_base_upgrades or not exclude_builder_attacks:
                            to_builder_base(ref_cache=True)

                        if not skip_builder_base_upgrades:
                            self.upgrader.collect_builder_attack_elixir()
                            self.upgrader.run_builder_base(exclude_builder_base, exclude_builder_lab)

                        if not exclude_builder_attacks:
                            success = self._run_builder_attack()
                            if success:
                                self.successful_attacks += 1
                            else:
                                self.failed_attacks += 1
                                cycle_success = False
                            self.total_attacks += 1

                        stop_coc()

                        if CLEAN_EMULATOR_ON_CYCLE:
                            clean_emulator_memory()

                        self.update_status(time.time())

                        # ── Resumo do ciclo ─────────────────────────────
                        s = self.session.summary()
                        print(
                            f"📊 Resumo acumulado: {s['total']} ataques | "
                            f"✅ {s['successes']} sucessos | "
                            f"❌ {s['failures']} falhas | "
                            f"Taxa: {s['rate']:.1f}%"
                        )

                        if not cycle_success:
                            if not self.quick_retry:
                                self.quick_retry = True
                                actual_wait = 10
                                print(f"⚠️ Falha no ciclo. Retry rápido em {actual_wait}s...")
                            else:
                                self.quick_retry = False
                                actual_wait = int(20 * random.uniform(0.9, 1.1))
                                print(f"⚠️ Segunda falha consecutiva. Próxima tentativa em {actual_wait}s...")
                        else:
                            self.quick_retry = False
                            actual_wait = (60 * CHECK_INTERVAL) * random.uniform(0.85, 1.15)
                            print(f"✅ Ciclo concluído. Próxima execução em ~{CHECK_INTERVAL} min.")

                        self.cycle_count += 1

                    if RESTART_EMULATOR_CYCLE_INTERVAL > 0 and self.cycle_count >= RESTART_EMULATOR_CYCLE_INTERVAL:
                        self.restart_bluestacks_flow()
                        self.cycle_count = 0

                    time.sleep(actual_wait)

                except (KeyboardInterrupt, SystemExit): raise
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    try:
                        stop_coc()
                    except Exception:
                        pass
                    self.update_status("error")
                    print(f"❌ Erro inesperado no ciclo principal: {e}. Aguardando antes de retentar...")
                    time.sleep(random.uniform(15, 45))

                    try:
                        self.start_bluestacks()
                        self.connect_adb()
                    except (KeyboardInterrupt, SystemExit): raise
                    except Exception as reconnect_error:
                        if configs.DEBUG:
                            print("Erro ao recuperar emulador/ADB:", reconnect_error)

        except (KeyboardInterrupt, SystemExit):
            print("\n🛑 Encerrando CoC Bot por solicitação do usuário...")
            self.session.print_report()
            raise
