from cv2 import utils
from utils import *
import configs
from configs import *

class Attacker:
    def __init__(self):
        self.assets = Asset_Manager.attacker_assets
        self.misc_assets = Asset_Manager.misc_assets
    
    # ============================================================
    # 📱 Screen Interaction
    # ============================================================
    
    def _click_okay(self, timeout=5):
        return click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["okay"], thresh=0.9),
            timeout=timeout,
        )
    
    def _click_surrender(self, timeout=5):
        return click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["surrender"], thresh=0.9),
            timeout=timeout
        )
    
    def _click_end_battle(self, timeout=5):
        return click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["end_battle"], thresh=0.9),
            timeout=timeout
        )
    
    def _click_return_home(self, timeout=5):
        return click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["return_home"], thresh=0.9),
            timeout=timeout
        )
    def start_normal_attack(self, timeout=120):
        import time
        print("Iniciando fluxo de ataque na Vila Principal...")
        
        # Limpeza preventiva inicial para fechar possíveis pop-ups tardios pós-carregamento
        time.sleep(1.5)
        clear_popups()
        time.sleep(1.0)

        def open_attack_and_start_matchmaking():
            attack_opened = False
            find_a_match_xy = (None, None)
            
            for attempt in range(3):
                print(f"Tentando abrir o menu de ataque (tentativa {attempt + 1}/3)...")
                Input_Handler.click(0.07, 0.9)
                time.sleep(1.0) # Aguarda a animação do menu lateral deslizar
                
                # Aguarda até 6 segundos para ver se o botão de 'Procurar Oponente' surge na tela
                start_check = time.time()
                while time.time() - start_check < 6:
                    xys = Frame_Handler.locate(self.assets["find_a_match"], thresh=0.82, return_all=True)
                    if len(xys) > 0:
                        xys = sorted(xys, key=lambda xy: xy[0])
                        x, y = xys[0]
                        if x <= 0.25:  # O painel multiplayer fica na parte esquerda
                            find_a_match_xy = (x, y)
                            attack_opened = True
                            break
                    time.sleep(0.3)
                    
                if attack_opened:
                    break
                    
                print("Menu de ataque não respondeu ou foi bloqueado por pop-ups. Executando limpeza...")
                clear_popups()
                time.sleep(1)
                
            if not attack_opened or find_a_match_xy[0] is None:
                print("Botão 'Procurar Oponente' não encontrado.")
                return False, None
                
            print("Botão 'Procurar Oponente' localizado com sucesso! Clicando...")
            Input_Handler.click(find_a_match_xy[0], find_a_match_xy[1])
            
            # Confirm attack
            print("Buscando confirmação de ataque (botão amarelo de ouro)...")
            if not click_with_timeout(
                lambda: Frame_Handler.locate(self.assets["confirm_attack"], thresh=0.85),
                timeout=6
            ): 
                print("Não foi possível confirmar o início da busca (confirm_attack não localizado).")
                return False, None
                
            return True, find_a_match_xy

        # Inicializa o matchmaking pela primeira vez
        success, find_a_match_xy = open_attack_and_start_matchmaking()
        if not success:
            return False

        # ----------------------------------------------------------------
        # Loop de matchmaking otimizado:
        # - Captura nova de tela a cada 1.5s (reduz carga ADB em ~67%)
        # - Cancela e retenta automaticamente após CLOUD_CANCEL_AFTER segundos
        # - Máximo de MAX_CANCEL_RETRIES cancelamentos no mesmo ciclo
        # ----------------------------------------------------------------
        CLOUD_CANCEL_AFTER = getattr(configs, 'CLOUD_CANCEL_AFTER', 25)   # segundos antes de cancelar e retentar
        MAX_CANCEL_RETRIES = getattr(configs, 'MAX_CANCEL_RETRIES', 2)    # máximo de cancelamentos por ciclo
        SCREENSHOT_INTERVAL = 1.5 # segundos entre capturas ADB

        for cancel_attempt in range(MAX_CANCEL_RETRIES + 1):
            if cancel_attempt == 0:
                print("Carregando o campo de batalha nas nuvens...")
            else:
                print(f"Reiniciando busca por oponente (tentativa {cancel_attempt + 1}/{MAX_CANCEL_RETRIES + 1})...")
                # Garante que a tela esteja limpa e reabre o menu de ataque a partir da Vila Principal
                clear_popups()
                time.sleep(1.0)
                success, find_a_match_xy = open_attack_and_start_matchmaking()
                if not success:
                    print("Não foi possível reconfirmar o ataque após cancelamento.")
                    break

            search_start = time.time()
            last_screenshot = 0.0
            frame = None

            while time.time() - search_start < CLOUD_CANCEL_AFTER:
                now = time.time()
                elapsed = int(now - search_start)

                # Captura nova tela apenas a cada SCREENSHOT_INTERVAL segundos
                if now - last_screenshot >= SCREENSHOT_INTERVAL:
                    frame = Frame_Handler.get_frame(grayscale=True)
                    last_screenshot = now
                elif frame is None:
                    time.sleep(SCREENSHOT_INTERVAL)
                    continue

                # Verifica botão End Battle (batalha carregada)
                x, y = Frame_Handler.locate(self.assets["end_battle"], frame=frame, thresh=0.75)
                if x is not None and y is not None:
                    print(f"Vila oponente carregada com sucesso! Batalha iniciada ({elapsed}s nas nuvens).")
                    return True

                # Verifica Surrender (já dentro da batalha — end_battle não capturado)
                sx, sy = Frame_Handler.locate(self.assets["surrender"], frame=frame, thresh=0.75)
                if sx is not None and sy is not None:
                    print(f"Batalha iniciada detectada via Surrender ({elapsed}s nas nuvens).")
                    return True

                # Verifica Return Home (Unable to attack village)
                rx, ry = Frame_Handler.locate(self.assets["return_home"], frame=frame, thresh=0.72)
                if rx is not None and ry is not None:
                    print("⚠️ Erro de conexão detectado: 'Unable to attack Village'. Retornando...")
                    Input_Handler.click(rx, ry)
                    time.sleep(1.5)
                    return False

                time.sleep(0.1)

            # Timeout parcial: tenta cancelar a busca e retentar
            if cancel_attempt < MAX_CANCEL_RETRIES:
                elapsed_total = int(time.time() - search_start)
                print(f"⏱️ Busca nas nuvens sem resposta após {elapsed_total}s. Cancelando e retentando...")
                
                # Clicar no botão de Cancelar/End Battle na tela de busca
                cx, cy = Frame_Handler.locate(self.assets["end_battle"], thresh=0.70)
                if cx is not None and cy is not None:
                    Input_Handler.click(cx, cy)
                    time.sleep(0.5)
                    # Confirma o cancelamento caso haja diálogo
                    ok_x, ok_y = Frame_Handler.locate(self.assets["okay"], thresh=0.80)
                    if ok_x is not None:
                        Input_Handler.click(ok_x, ok_y)
                    time.sleep(1.5)
                else:
                    # Se não achar o botão cancelar, tenta tecla voltar via ADB
                    print("Botão cancelar não encontrado na tela. Enviando tecla Voltar...")
                    if utils.ADB_DEVICE is not None:
                        utils.ADB_DEVICE.shell("input keyevent 4")
                    else:
                        print("⚠️ Dispositivo ADB não conectado para enviar comando de voltar.")
                    time.sleep(2.0)
            else:
                print(f"❌ Limite de {MAX_CANCEL_RETRIES} retentativas atingido. Desistindo da busca.")

        return False
    
    def start_builder_attack(self, timeout=60):
        import time
        
        # Click attack
        Input_Handler.click(0.07, 0.9)
        
        # Find a match
        if not click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["find_now"], thresh=0.9),
            timeout=5
        ): return False
        
        # Wait until "battle starts in" text is found
        start_time = time.time()
        while time.time() - start_time < timeout:
            section = Frame_Handler.get_frame_section(0, 0, 1, 0.1, grayscale=True, high_contrast=True, thresh=150)
            x, y = Frame_Handler.locate(self.assets["battle_starts_in"], section, thresh=0.9)
            if x is not None and y is not None: return True
            time.sleep(0.1)
        return False
    
    def detect_troop_positions(self, frame, clip_left=0.0, clip_right=1.0, type_gaps_seen=0, return_boundaries=False, return_types=False, return_counts=False):
        import cv2, scipy, numpy as np
        
        # Retorno vazio seguro — espelha exatamente a estrutura do output normal
        # para que o unpack no caller (card_centers, boundaries, types, counts, type_gaps_seen)
        # nunca falhe independente de quais flags de retorno estão ativas.
        def _empty_output():
            out = [np.array([])]
            if return_boundaries: out.append([])
            if return_types: out.append([])
            if return_counts: out.append([])
            out.append(type_gaps_seen)
            return out

        # Validação defensiva do frame (substitui assert que propagava exceção silenciosa)
        if not (len(frame.shape) == 3 and frame.shape[2] == 3):
            print("⚠️ [detect_troop_positions] Frame inválido (esperado RGB 3 canais). Retornando vazio.")
            return _empty_output() if (return_boundaries or return_types or return_counts) else np.array([])

        try:
            # Look for vertical card edges
            frame_color = frame.copy()
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            orig_h, orig_w = frame_gray.shape
            frame_color = frame_color[:, max(0, int(orig_w*clip_left)-10):min(orig_w, int(orig_w*clip_right)+10)]
            frame_gray = frame_gray[:, max(0, int(orig_w*clip_left)-10):min(orig_w, int(orig_w*clip_right)+10)]
            frame_gray = cv2.equalizeHist(frame_gray)
            edges = cv2.convertScaleAbs(np.abs(cv2.Sobel(frame_gray, cv2.CV_64F, 1, 0, ksize=3)))
            profile = np.sum(edges, axis=0)
            profile = (profile - profile.min()) / (profile.max() - profile.min())
            peaks = scipy.signal.find_peaks(profile, height=0.8, distance=10)[0]
            peaks_norm = peaks / orig_w + clip_left
            
            # Verificação mínima de peaks detectados antes de processar distâncias
            if len(peaks_norm) < 2:
                print(f"⚠️ [detect_troop_positions] Poucos peaks detectados ({len(peaks_norm)}). Tela pode não estar carregada.")
                return _empty_output() if (return_boundaries or return_types or return_counts) else np.array([])
            
            # Compute distances between edges and discretize
            dists = np.diff(peaks_norm)
            dist_categories = np.array([0.007, 0.015, 0.068]) # normal gap, type change gap, card width
            tol = 0.01
            diffs = np.abs(dists[:, None] - dist_categories)
            closest_idx = np.argmin(diffs, axis=1)
            closest_dist = diffs[np.arange(len(dists)), closest_idx]
            dists_discrete = dist_categories[closest_idx]
            dists_discrete[closest_dist > tol] = np.nan
            
            # Remove partially visible card edges (com checagem defensiva para dists_discrete vazio)
            if len(dists_discrete) == 0:
                print("⚠️ [detect_troop_positions] dists_discrete vazio após discretização. Retornando vazio.")
                return _empty_output() if (return_boundaries or return_types or return_counts) else np.array([])

            remove_left = 0
            remove_right = len(dists_discrete) - 1
            # Protege contra loop infinito caso nenhuma borda de card seja encontrada
            while remove_left < len(dists_discrete) and dists_discrete[remove_left] != dist_categories[2]:
                remove_left += 1
            while remove_right >= 0 and dists_discrete[remove_right] != dist_categories[2]:
                remove_right -= 1
            
            if remove_left >= remove_right:
                print(f"⚠️ [detect_troop_positions] Nenhuma borda completa de card detectada (remove_left={remove_left}, remove_right={remove_right}).")
                return _empty_output() if (return_boundaries or return_types or return_counts) else np.array([])

            peaks = peaks[remove_left:remove_right+2]
            peaks_norm = peaks_norm[remove_left:remove_right+2]
            dists_discrete = dists_discrete[remove_left:remove_right+1]
            
            # Verifica paridade dos peaks (substitui assert que causava exceção silenciosa)
            if len(peaks) % 2 != 0:
                print(f"⚠️ [detect_troop_positions] Número ímpar de bordas de slot ({len(peaks)}). Descartando última borda.")
                peaks = peaks[:-1]
                peaks_norm = peaks_norm[:-1]
            
            # Convert edge distances to card locations
            card_types = []
            card_centers = []
            card_boundaries = []
            card_counts = []
            for card_idx in range(0, len(peaks_norm), 2):  # ← FIX: variável 'card_idx' em vez de 'i' para não colidir com loop interno
                x = (peaks_norm[card_idx] + peaks_norm[card_idx+1]) / 2
                card_centers.append(x)
                card_boundaries.extend([peaks_norm[card_idx], peaks_norm[card_idx+1]])
                prev_gap = dists_discrete[card_idx-1] if card_idx-1 > 0 else dist_categories[0]
                next_gap = dists_discrete[card_idx+1] if card_idx+1 < len(dists_discrete) else dist_categories[0]
                if prev_gap == dist_categories[1]: type_gaps_seen += 1
                
                # Figure out whether card is a normal troop, clan troop, or hero
                card_section = frame_color[:, peaks[card_idx]:peaks[card_idx+1]]
                card_section_gray = frame_gray[:, peaks[card_idx]:peaks[card_idx+1]]
                h, w = card_section_gray.shape[:2]
                card_texture = cv2.Canny(card_section_gray, 50, 150) / 255
                x_asset = render_text("x", "SupercellMagic", 25)
                x_h, x_w = x_asset.shape[:2]
                x_sign_loc = Frame_Handler.locate(x_asset, card_section_gray, grayscale=True, thresh=0.75, ref="lc")
                if x_sign_loc[0] is not None and x_sign_loc[1] is not None: # Only troops, clan troops, or spells have multiplicity
                    count_section = card_section_gray[:int(h*x_sign_loc[1]+0.5*x_h)+1, int(w*x_sign_loc[0]+x_w)-1:]
                    number_locs = Frame_Handler.batch_locate([render_text(str(n), "SupercellMagic", 25) for n in range(0, 12)], frame=count_section, grayscale=True, thresh=0.8, ref="cc")
                    
                    count = 1
                    # ← FIX: variável interna 'n_val' em vez de 'i' para não sobrescrever 'card_idx'
                    for n_val in reversed(range(0, 12)):
                        loc = number_locs[n_val]
                        if loc[0] is not None and loc[1] is not None:
                            count = n_val
                            break
                    
                    # Clan troops either have a clan badge rather than a smooth background
                    # or will have wider card edge gaps compared to typical troops
                    if max(card_texture[int(h*x_sign_loc[1])-10:int(h*x_sign_loc[1])+10, :int(w*x_sign_loc[0]-1)].mean(1)) > 0.1:
                        card_type = "clan"
                        card_counts.append(1)
                    elif prev_gap == dist_categories[1] and next_gap == dist_categories[1]:
                        card_type = "clan"
                        card_counts.append(1)
                    elif type_gaps_seen > 0:
                        card_type = "spell"
                        card_counts.append(count)
                    else:
                        card_type = "troop"
                        card_counts.append(-1)
                else:
                    card_section_border = card_section.copy()
                    card_section_border[int(h*0.1):int(h*0.9), int(w*0.1):int(w*0.9)] = 0
                    mask = filter_color((68, 202, 222), card_section_border, tol=100, return_mask=True)[1]
                    blue_pct = mask.mean()
                    # Siege machine doesn't have multiplicity anymore
                    if blue_pct > 0.1:
                        card_type = "clan"
                        card_counts.append(1)
                    else:
                        card_type = "hero"
                        card_counts.append(1)
                card_types.append(card_type)

            card_centers = np.array(card_centers)
            print(f"🔍 [detect_troop_positions] {len(card_centers)} card(s) detectado(s): {card_types}")
            
            if not return_boundaries and not return_types: return card_centers
            
            output = [card_centers]
            if return_boundaries: output.append(card_boundaries)
            if return_types: output.append(card_types)
            if return_counts: output.append(card_counts)
            output.append(type_gaps_seen)
            return output

        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            import configs
            if configs.DEBUG:
                import traceback
                print(f"⚠️ [detect_troop_positions] Exceção inesperada: {e}")
                traceback.print_exc()
            return _empty_output() if (return_boundaries or return_types or return_counts) else np.array([])
    
    def deploy_troops(self, card_centers, available_slots=None, card_types=None, card_counts=None):
        import time, numpy as np, random
        
        def card_gray(card_center):
            section = Frame_Handler.get_frame_section(card_center-0.01, 0.89, card_center+0.01, 0.91, grayscale=False)
            return np.all(section[:, :, 0] == section[:, :, 1]) and np.all(section[:, :, 1] == section[:, :, 2])
        
        if available_slots is None: available_slots = [1] * len(card_centers)
        if card_types is None: card_types = [None] * len(card_centers)
        if card_counts is None: card_counts = [0] * len(card_centers)
        
        active_count = sum(available_slots)
        if active_count == 0:
            print("⚠️ [deploy_troops] Nenhum slot ativo para deploy. Pulando.")
            return
        
        print(f"⚔️ [deploy_troops] Iniciando deploy de {active_count} grupo(s). Slots disponíveis: {list(available_slots)}")
        
        # ─── FIX Bug #3: sleep após down(pointer=1) para garantir que o hold está
        # ativo no minitouch ANTES de enviar os clicks de seleção de card.
        # Sem este sleep, o click chega ao servidor minitouch antes do down, causando
        # inputs fora de ordem e deploy em posições erradas.
        hold_x = 0.5 + random.uniform(-0.05, 0.05)
        hold_y = 0.8 + random.uniform(-0.05, 0.05)
        Input_Handler.down(hold_x, hold_y, pointer=1)
        time.sleep(0.30)  # aguarda minitouch registrar o hold (era 0.1–0.25, insuficiente)
        
        for slot_idx in range(len(card_centers)):
            if not available_slots[slot_idx]:
                continue
            
            slot_type = card_types[slot_idx] if card_types[slot_idx] else "desconhecido"
            slot_count = card_counts[slot_idx]
            print(f"   → Slot {slot_idx+1}/{len(card_centers)} | tipo={slot_type} | qtd={slot_count} | x={card_centers[slot_idx]:.3f}")
            
            # Delay variável antes de interagir com o slot
            time.sleep(random.uniform(0.12, 0.32))
            
            # Seleciona o card no menu inferior (com leve ruído para simular toque humano)
            card_click_x = card_centers[slot_idx] + random.uniform(-0.008, 0.008)
            card_click_y = 0.9 + random.uniform(-0.01, 0.01)
            Input_Handler.click(card_click_x, card_click_y)
            time.sleep(random.uniform(0.15, 0.30))  # aguarda o card ser selecionado na UI
            
            # Coordenada de deploy no campo (ligeiramente variada por slot)
            deploy_x = 0.5 + random.uniform(-0.06, 0.06)
            deploy_y = 0.8 + random.uniform(-0.06, 0.06)
            
            if slot_type in ["hero", "clan"]:
                print(f"     [deploy] {slot_type.upper()} → clique único em ({deploy_x:.3f}, {deploy_y:.3f})")
                Input_Handler.click(deploy_x, deploy_y)
            elif slot_type == "troop":
                deploy_time = configs.TROOP_DEPLOY_TIME * random.uniform(0.85, 1.15)
                print(f"     [deploy] TROOP → hold por {deploy_time:.2f}s em ({deploy_x:.3f}, {deploy_y:.3f})")
                Input_Handler.down(deploy_x, deploy_y, pointer=0)
                end_time = time.monotonic() + deploy_time
                while time.monotonic() < end_time and not card_gray(card_centers[slot_idx]):
                    time.sleep(0.01)
                Input_Handler.up(pointer=0)
            elif slot_type == "spell":
                n_spell = card_counts[slot_idx]
                print(f"     [deploy] SPELL → {n_spell} lançamento(s) dispersos")
                rxs = np.random.uniform(0.35, 0.65, n_spell)
                rys = np.random.uniform(0.45, 0.55, n_spell)
                for coord in zip(rxs, rys):
                    Input_Handler.click(coord[0] + random.uniform(-0.02, 0.02), coord[1] + random.uniform(-0.02, 0.02))
                    time.sleep(random.uniform(0.1, 0.25))
            else:
                n_clicks = max(0, card_counts[slot_idx])
                print(f"     [deploy] TIPO DESCONHECIDO → {n_clicks} clique(s) em ({deploy_x:.3f}, {deploy_y:.3f})")
                for _ in range(n_clicks):
                    Input_Handler.click(deploy_x + random.uniform(-0.03, 0.03), deploy_y + random.uniform(-0.03, 0.03))
                    time.sleep(random.uniform(0.08, 0.18))
            
            # Delay de estabilização pós-deploy do slot
            time.sleep(random.uniform(0.15, 0.35))
        
        # Release secondary pointer
        Input_Handler.up(pointer=1)
        time.sleep(random.uniform(0.1, 0.25))
        
        # Unselect last card (clique em área vazia à esquerda)
        unselect_x = 0.01 + random.uniform(0, 0.015)
        unselect_y = 0.9 + random.uniform(-0.02, 0.02)
        Input_Handler.click(unselect_x, unselect_y)
        print(f"✅ [deploy_troops] Deploy concluído. {active_count} grupo(s) enviados ao campo.")
    
    def complete_normal_attack(self, restart=True, exclude_clan_troops=False):
        import time, numpy as np, gc
        print("Preparando posicionamento tático (zoom out + scroll up)...")
        
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_up()
        
        type_gaps_seen = 0
        total_slots_seen = 0
        last_card_left = 0.0
        deploy_iterations = 0
        MAX_DEPLOY_ITERATIONS = 20  # segurança contra loop infinito
        
        print(f"🗺️ [complete_normal_attack] Iniciando varredura de slots. Range alvo: {ATTACK_SLOT_RANGE}")
        
        while total_slots_seen < ATTACK_SLOT_RANGE[1] - ATTACK_SLOT_RANGE[0] + 1:
            if deploy_iterations >= MAX_DEPLOY_ITERATIONS:
                print(f"⚠️ [complete_normal_attack] Limite de {MAX_DEPLOY_ITERATIONS} iterações de deploy atingido. Encerrando varredura.")
                break
            deploy_iterations += 1
            
            gc.collect()
            frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
            
            # ─── FIX Bug #2: encapsula detect em try/except para não perder o ataque
            # por exceção silenciosa (anteriormente assert levantava erro não tratado)
            try:
                result = self.detect_troop_positions(
                    frame,
                    clip_left=last_card_left,
                    type_gaps_seen=type_gaps_seen,
                    return_boundaries=True,
                    return_types=True,
                    return_counts=True
                )
                card_centers, card_boundaries, card_types, card_counts, type_gaps_seen = result
            except Exception as e:
                print(f"⚠️ [complete_normal_attack] Falha ao detectar posições de tropas (iteração {deploy_iterations}): {e}. Encerrando varredura.")
                break
            
            if len(card_centers) == 0:
                print(f"ℹ️ [complete_normal_attack] Nenhum card detectado na iteração {deploy_iterations}. Encerrando varredura.")
                break

            print(f"📋 [complete_normal_attack] Iteração {deploy_iterations}: {len(card_centers)} card(s) visíveis. Total acumulado: {total_slots_seen}")

            # Exclude clan troops if specified
            available_slots = np.ones_like(card_centers)
            if exclude_clan_troops:
                for slot_i, card_type in enumerate(card_types):
                    if card_type == "clan":
                        available_slots[slot_i] = 0
                        print(f"   Slot {slot_i+1} excluído (tropa de clã).")
            
            # Exclude troops outside of specified slot range
            available_slots[:max(0, ATTACK_SLOT_RANGE[0] - total_slots_seen)] = 0
            available_slots[max(0, ATTACK_SLOT_RANGE[1] + 1 - total_slots_seen):] = 0
            
            # Deploy troops up until the last one visible
            total_slots_seen += len(card_centers) - 1
            self.deploy_troops(card_centers[:-1], available_slots[:-1], card_types[:-1], card_counts[:-1])
            
            # Scroll over and look for the new position of the last card
            last_card_frame = frame[:, int(card_boundaries[-2] * frame.shape[1]):int(card_boundaries[-1] * frame.shape[1])]
            print(f"   Scrollando para encontrar próximo card (x: {card_centers[-1]:.3f} → 0.038)...")
            Input_Handler.swipe_left(x1=card_centers[-1], x2=0.038, y=0.9, hold_end_time=500)
            time.sleep(0.5)
            frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
            last_card_left = Frame_Handler.locate(last_card_frame, frame, thresh=0.9, grayscale=False, ref="lc")[0]
            
            # If the card didn't move then there are no more troops so it can be deployed
            if last_card_left is not None and abs(last_card_left - card_boundaries[-2]) < 0.01:
                print(f"   Último card não se moveu — todos os slots varridos. Deployando último card.")
                self.deploy_troops(card_centers[-1:], available_slots[-1:], card_types[-1:], card_counts[-1:])
                break
            elif last_card_left is None:
                print("   Último card não localizado após scroll. Encerrando varredura.")
                break
        
        # Close and reopen CoC to auto complete battle
        if AUTO_COMPLETE_BATTLE:
            import random
            wait_time = random.uniform(2.5, 5.5)
            print(f"Toda a estratégia militar foi enviada ao campo. Aguardando {wait_time:.1f} segundos para sincronização dos pacotes...")
            time.sleep(wait_time)
            print("Reiniciando o app para computar o ataque (Auto-Complete)...")
            if restart:
                start_coc()
            else:
                stop_coc()
        else:
            print("AUTO_COMPLETE_BATTLE desativado. Aguardando o fim da batalha na tela (modo simulação humana)...")
            start_wait = time.time()
            battle_finished = False
            last_print_time = start_wait
            while time.time() - start_wait < 210:
                now = time.time()
                elapsed = int(now - start_wait)
                if now - last_print_time >= 10:
                    print(f"Aguardando fim da batalha... (decorrido: {elapsed} segundos)")
                    last_print_time = now
                
                ox, oy = Frame_Handler.locate(self.assets["okay"], thresh=0.8)
                if ox is not None and oy is not None:
                    print("Batalha finalizada (botão Okay detectado). Retornando para a vila.")
                    Input_Handler.click(ox, oy)
                    battle_finished = True
                    break
                
                rx, ry = Frame_Handler.locate(self.assets["return_home"], thresh=0.8)
                if rx is not None and ry is not None:
                    print("Batalha finalizada (botão Return Home detectado). Retornando para a vila.")
                    Input_Handler.click(rx, ry)
                    battle_finished = True
                    break
                
                time.sleep(2)
            if not battle_finished:
                print("Tempo limite excedido esperando o fim da batalha. Forçando encerramento.")
                if restart:
                    start_coc()
                else:
                    stop_coc()
    
    def complete_builder_attack(self, restart=True):
        import numpy as np
        import time
        
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_up()
        
        card_centers = np.linspace(0.1, 0.9, 11)
        self.deploy_troops(card_centers, card_counts=[4]*len(card_centers))
        
        # Close and reopen CoC to auto complete battle
        if AUTO_COMPLETE_BATTLE:
            import random
            wait_time = random.uniform(2.5, 5.5)
            print(f"Toda a estratégia militar foi enviada ao campo. Aguardando {wait_time:.1f} segundos para sincronização dos pacotes...")
            time.sleep(wait_time)
            print("Reiniciando o app para computar o ataque (Auto-Complete)...")
            if restart:
                start_coc()
            else:
                stop_coc()
        else:
            print("AUTO_COMPLETE_BATTLE desativado. Aguardando o fim da batalha na tela (modo simulação humana)...")
            start_wait = time.time()
            battle_finished = False
            last_print_time = start_wait
            while time.time() - start_wait < 210:
                now = time.time()
                elapsed = int(now - start_wait)
                if now - last_print_time >= 10:
                    print(f"Aguardando fim da batalha... (decorrido: {elapsed} segundos)")
                    last_print_time = now
                
                ox, oy = Frame_Handler.locate(self.assets["okay"], thresh=0.8)
                if ox is not None and oy is not None:
                    print("Batalha do construtor finalizada (botão Okay detectado). Retornando para a vila.")
                    Input_Handler.click(ox, oy)
                    battle_finished = True
                    break
                
                rx, ry = Frame_Handler.locate(self.assets["return_home"], thresh=0.8)
                if rx is not None and ry is not None:
                    print("Batalha do construtor finalizada (botão Return Home detectado). Retornando para a vila.")
                    Input_Handler.click(rx, ry)
                    battle_finished = True
                    break
                
                time.sleep(2)
            if not battle_finished:
                print("Tempo limite excedido esperando o fim da batalha. Forçando encerramento.")
                if restart:
                    start_coc()
                else:
                    stop_coc()
    
    # ============================================================
    # ⚔️ Attack Management
    # ============================================================

    @require_exit()
    def run_home_base(self, timeout=120, restart=True):
        import time
        
        try:
            # Make sure in home base
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    get_home_builders(1)
                    break
                except (KeyboardInterrupt, SystemExit): raise
                except: pass
            if time.time() - start_time >= timeout:
                print("Erro ao validar Vila Principal para ataque (Timeout).")
                return False
            
            # Complete an attack
            if self.start_normal_attack(timeout):
                self.complete_normal_attack(restart=restart, exclude_clan_troops=EXCLUDE_CLAN_TROOPS)
                print("Ataque na Vila Principal concluído com sucesso!")
                return True
            else:
                print("Ataque na Vila Principal não realizado (Oponente não encontrado ou erro de carregamento).")
                return False
        
        except Exception as e:
            print(f"Erro crítico durante o ataque na Vila Principal: {e}")
            return False

    @require_exit()
    def run_builder_base(self, timeout=60, restart=True):
        import time
        
        try:
            # Make sure in builder base
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    get_builder_builders(1)
                    break
                except (KeyboardInterrupt, SystemExit): raise
                except: pass
            if time.time() - start_time >= timeout:
                print("Erro ao validar Vila do Construtor para ataque (Timeout).")
                return False
            
            # Complete an attack
            if self.start_builder_attack(timeout):
                self.complete_builder_attack(restart=restart)
                print("Ataque na Vila do Construtor concluído com sucesso!")
                return True
            else:
                print("Ataque na Vila do Construtor não realizado (Oponente não encontrado ou erro de carregamento).")
                return False
        
        except Exception as e:
            print(f"Erro crítico durante o ataque na Vila do Construtor: {e}")
            return False
