import utils
from utils import *
from configs import *
from upgrader import Upgrader
from attacker import Attacker
import random

class CoC_Bot:
    def __init__(self):
        self.cycle_count = 0
        self.total_attacks = 0
        self.successful_attacks = 0
        self.failed_attacks = 0
        self.quick_retry = False
        pre_init_ocr()
        self.start_bluestacks()
        self.connect_adb()
        self.upgrader = Upgrader()
        self.attacker = Attacker()

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
        import sys, subprocess, time
        
        if self.check_bluestacks():
            if configs.DEBUG: print("BlueStacks is already running.")
            return
        
        if sys.platform == "darwin":
            subprocess.Popen([
                "osascript", "-e",
                'tell application "BlueStacks" to launch\n'
                'tell application "BlueStacks" to set visible of front window to false'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 6
            subprocess.Popen([r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
        
        for _ in range(120):
            if self.check_bluestacks():
                if configs.DEBUG: print("BlueStacks started.")
                return
            time.sleep(0.5)
        
        raise Exception("BlueStacks failed to start.")
    
    def check_bluestacks(self):
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name']:
                name = proc.info['name'].lower()
                if 'bluestacks' in name or 'hd-player' in name:
                    return True
        return False

    def connect_adb(self):
        import time
        for _ in range(120):
            try:
                connect_adb()
                if configs.DEBUG: print("Connected to ADB.")
                return
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("connect_adb", e)
            time.sleep(0.5)
        raise Exception("Failed to connect to ADB.")
    
    def restart_bluestacks_flow(self):
        import subprocess, time, sys
        
        print("\n=== Reiniciando o BlueStacks preventivamente para liberar memória RAM ===")
        self.update_status("restarting")
        
        try:
            stop_coc()
        except:
            pass
            
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "HD-Player.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == "darwin":
            subprocess.run(["osascript", "-e", 'quit application "BlueStacks"'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        print("Aguardando 5 segundos para liberação dos recursos no sistema operacional...")
        time.sleep(5)
        
        self.start_bluestacks()
        self.connect_adb()
        print("=== BlueStacks reiniciado e ADB reconectado com sucesso ===\n")
    
    # ============================================================
    # ⏱️ Task Execution
    # ============================================================
    
    def run(self):
        import time
        import gc
        
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
                    
                    # Check home base
                    if not skip_home_base_upgrades or not exclude_home_attacks:
                        to_home_base(ref_cache=True)
                    
                    if not skip_home_base_upgrades:
                        self.upgrader.run_home_base(exclude_home_base, exclude_home_lab)
                    if not exclude_home_attacks:
                        success = self.attacker.run_home_base(restart=not skip_home_base_upgrades or not skip_builder_base_upgrades)
                        if success:
                            self.successful_attacks += 1
                        else:
                            self.failed_attacks += 1
                            cycle_success = False
                        self.total_attacks += 1
                    
                    # Check builder base
                    if not skip_builder_base_upgrades or not exclude_builder_attacks:
                        to_builder_base(ref_cache=True)
                    
                    if not skip_builder_base_upgrades:
                        self.upgrader.collect_builder_attack_elixir()
                        self.upgrader.run_builder_base(exclude_builder_base, exclude_builder_lab)
                    if not exclude_builder_attacks:
                        success = self.attacker.run_builder_base()
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
                    print(f"Resumo acumulado: {self.total_attacks} ataques | {self.successful_attacks} sucessos | {self.failed_attacks} falhas")
                    
                    if not cycle_success:
                        if not self.quick_retry:
                            self.quick_retry = True
                            actual_wait = 10
                            print(f"Falha de ataque detectada. Agendando retry rápido em {actual_wait} segundos...")
                        else:
                            self.quick_retry = False
                            actual_wait = int(20 * random.uniform(0.9, 1.1))
                            print(f"Segunda falha detectada. Agendando nova tentativa rápida em {actual_wait} segundos...")
                    else:
                        self.quick_retry = False
                        actual_wait = (60 * CHECK_INTERVAL) * random.uniform(0.85, 1.15)
                        print(f"Ciclo concluído com sucesso. Próxima execução em aproximadamente {CHECK_INTERVAL} minutos.")
                        
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
                except:
                    pass
                self.update_status("error")
                # Em caso de erro, espera um tempo variável antes de tentar reiniciar
                time.sleep(random.uniform(15, 45))
                
                # Tenta restabelecer a conexão com o emulador e ADB
                try:
                    self.start_bluestacks()
                    self.connect_adb()
                except (KeyboardInterrupt, SystemExit): raise
                except Exception as reconnect_error:
                    if configs.DEBUG: print("Erro ao tentar recuperar emulador/ADB:", reconnect_error)
