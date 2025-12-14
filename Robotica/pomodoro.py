import time

# --- DEFINIÇÃO DOS NÚMEROS (Pixel Art 5x7) ---
DIGITS = {
    0: [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    1: [[0,0,1,0,0],[0,1,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,1,1,1,0]],
    2: [[0,1,1,1,0],[1,0,0,0,1],[0,0,0,0,1],[0,0,1,1,0],[0,1,0,0,0],[1,0,0,0,0],[1,1,1,1,1]],
    3: [[1,1,1,1,0],[0,0,0,0,1],[0,0,1,1,0],[0,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    4: [[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,1],[0,0,0,0,1],[0,0,0,0,1],[0,0,0,0,1]],
    5: [[1,1,1,1,1],[1,0,0,0,0],[1,1,1,1,0],[0,0,0,0,1],[0,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    6: [[0,1,1,1,0],[1,0,0,0,0],[1,0,0,0,0],[1,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    7: [[1,1,1,1,1],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]],
    8: [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    9: [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,1],[0,0,0,0,1],[0,0,0,0,1],[0,1,1,1,0]]
}

def create_led_frame(number):
    ON_COLOR = [255, 255, 255]
    OFF_COLOR = [0, 0, 0]
    tens = number // 10
    units = number % 10
    grid = []
    for row_idx in range(13):
        row_colors = []
        if 3 <= row_idx < 10:
            digit_row = row_idx - 3
            row_colors.append(OFF_COLOR)
            for p in DIGITS.get(tens, DIGITS[0])[digit_row]: row_colors.append(ON_COLOR if p else OFF_COLOR)
            row_colors.append(OFF_COLOR)
            for p in DIGITS.get(units, DIGITS[0])[digit_row]: row_colors.append(ON_COLOR if p else OFF_COLOR)
            row_colors.append(OFF_COLOR)
        else:
            for _ in range(13): row_colors.append(OFF_COLOR)
        row_colors.reverse()
        grid.extend(row_colors)
    return grid

def get_sensors(robot):
    try:
        status = robot.status()
        if status is None: return False, False
        chest = status.get('touch_chest', False)
        h_n = status.get('touch_head_n', False)
        h_s = status.get('touch_head_s', False)
        h_e = status.get('touch_head_e', False)
        h_w = status.get('touch_head_w', False)
        return (h_n or h_s or h_e or h_w), chest
    except: return False, False

def setup_pomodoro(robot):
    """
    FASE 1: Configuração. 
    Retorna o número de minutos escolhidos (int).
    """
    print("--- POMODORO SETUP ---")
    robot.set_screen(text="SETUP MODE")
    options = [30, 35, 40, 45, 50]
    idx = 0
    TIMEOUT = 10
    
    try: robot.update_leds(create_led_frame(options[idx]))
    except: pass
    
    last_head = False
    last_interaction = time.time()
    last_disp = -1
    
    while True:
        try:
            head, chest = get_sensors(robot)
            remaining = int(TIMEOUT - (time.time() - last_interaction))
            
            # Auto-start
            if remaining < 0: 
                print(" -> Auto-start!")
                return options[idx] 
            
            if remaining != last_disp:
                print(f"Auto-start: {remaining}s")
                robot.set_screen(text=f"Auto-start in\n{remaining}")
                last_disp = remaining

            # Mudar Tempo
            if head and not last_head:
                idx = (idx + 1) % len(options)
                val = options[idx]
                print(f"Tempo: {val} min")
                robot.update_leds(create_led_frame(val))
                robot.set_screen(text=f"Time: {val} min")
                last_interaction = time.time()
                last_disp = -1
                
                # Safety lock
                while True: 
                    h, _ = get_sensors(robot)
                    if not h: break
                    time.sleep(0.1)
                time.sleep(0.5)
                continue

            # Confirmar
            if chest: 
                print(" -> Confirmado!")
                return options[idx]
                
            last_head = head
            time.sleep(0.1)
        except: time.sleep(0.5)

def run_countdown_leds(robot, minutes, stop_event):
    """
    FASE 2: Contagem decrescente apenas nos LEDs.
    Recebe um 'stop_event' para saber quando parar se o programa principal fechar.
    """
    total_seconds = minutes * 60
    # total_seconds = 60 # Descomenta para testar rápido (1 min)
    
    print(f"--- INICIOU TIMER DE {minutes} MINUTOS ---")
    
    while total_seconds >= 0 and not stop_event.is_set():
        mins_left = total_seconds // 60
        
        # Atualiza LEDs a cada minuto exato
        if total_seconds % 60 == 0:
            print(f"LEDs: {mins_left}")
            try: robot.update_leds(create_led_frame(mins_left))
            except: pass
            
        time.sleep(1)
        total_seconds -= 1
        
    print("--- FIM DO TEMPO ---")
    robot.set_screen(text="TIME IS UP!")
    
    # Piscar final
    RED, BLACK = [255, 0, 0], [0, 0, 0]
    for _ in range(5):
        if stop_event.is_set(): break
        try:
            robot.update_leds(RED * 169)
            time.sleep(0.5)
            robot.update_leds(BLACK * 169)
            time.sleep(0.5)
        except: pass