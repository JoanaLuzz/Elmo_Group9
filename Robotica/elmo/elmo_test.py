import sys
import time
import threading
from ElmoV2API import ElmoV2API
from eye_tracker import EyeTracker

def monitor_attention(robot, tracker, stop_event):
    """
    Vigia: Focado, Distraído e Zoning Out.
    Zoning Out e Distraído têm o mesmo comportamento (Triste + Cabeça Baixo).
    Focado recupera (Feliz -> Normal + Cabeça Centro).
    """
    print(" -> [Thread] Vigilância iniciada (Zoning = Distraído).")
    current_mood = "normal"
    
    # Estado Inicial
    try:
        robot.set_screen(image="normal.png")
        robot.set_tilt(0)
    except:
        print(" -> [Aviso] Falha inicial.")
    
    count_bad = 0      # Conta frames de Distração ou Zoning
    count_good = 0     # Conta frames de Foco
    STABILITY_LIMIT = 3
    
    # Histórico para Zoning Out
    gaze_history = [] 
    HISTORY_SIZE = 10  # 5 segundos (10 * 0.5s)

    while not stop_event.is_set():
        is_looking = tracker.is_focused()
        current_ratio = tracker.get_iris_ratio()
        
        # 1. Atualizar histórico e calcular Zoning Out
        gaze_history.append(current_ratio)
        if len(gaze_history) > HISTORY_SIZE:
            gaze_history.pop(0)

        is_zoning_out = False
        if len(gaze_history) == HISTORY_SIZE:
            variation = max(gaze_history) - min(gaze_history)
            # Se a variação for minúscula, está vidrado
            if variation < 0.015: 
                is_zoning_out = True

        # --- LÓGICA DE DECISÃO UNIFICADA ---
        
        # O utilizador está a "falhar" se estiver distraído OU em zoning out
        is_behaving_badly = (not is_looking) or is_zoning_out

        if is_behaving_badly:
            count_bad += 1
            count_good = 0
            
            if count_bad >= STABILITY_LIMIT:
                if current_mood != "sad":
                    reason = "ZONING OUT" if is_zoning_out else "DISTRAIDO"
                    print(f"\n -> [Eye] {reason}! A ficar triste e baixar cabeça...")
                    
                    # Comportamento de Tristeza (Igual para ambos)
                    robot.set_tilt(15)  # Cabeça para baixo
                    robot.set_screen(image="sad_eyes.jpeg")
                    # AUDIO
                    robot.play_sound("Sad.wav")
                    
                    current_mood = "sad"
                count_bad = STABILITY_LIMIT # Manter no máximo

        else: # Está focado (e não está em zoning out)
            count_good += 1
            count_bad = 0
            
            if count_good >= STABILITY_LIMIT:
                if current_mood != "normal":
                    print("\n -> [Eye] Recuperou o foco! A festejar...")
                    
                    # 1. Levanta a cabeça
                    robot.set_tilt(0)
                    
                    # 2. Se estava triste antes, mostra felicidade primeiro
                    if current_mood == "sad":
                        robot.set_screen(image="happy_eyes.jpeg")
                        # AUDIO
                        robot.play_sound("Happy.wav")
                        time.sleep(2.5) # Tempo para mostrar a felicidade
                    
                    # 3. Volta ao normal
                    print(" -> [Eye] A voltar ao trabalho (Normal).")
                    robot.set_screen(image="normal.png")
                    
                    current_mood = "normal"
                count_good = STABILITY_LIMIT

        # Debug print para saberes o que está a acontecer
        state_txt = "ZONING" if is_zoning_out else ("DISTRAIDO" if not is_looking else "FOCADO")
        print(f" -> Olho: {current_ratio:.3f} | Var: {max(gaze_history)-min(gaze_history):.3f} | Estado: {state_txt}   ", end='\r')

        time.sleep(0.5)
    
    print("\n -> [Thread] Vigilância terminada.")
    """
    Vigia: Focado, Distraído e Zoning Out (Olhar fixo/vidrado).
    """
    print(" -> [Thread] Vigilância iniciada (Com Zoning Out).")
    current_mood = "normal"
    
    try:
        robot.set_screen(image="normal.png")
        robot.set_tilt(0)
    except:
        print(" -> [Aviso] Falha inicial.")
    
    count_focused = 0
    count_distracted = 0
    STABILITY_LIMIT = 3
    
    # [NOVO] Lista para guardar o histórico do olhar (últimos 5 segundos)
    gaze_history = [] 
    HISTORY_SIZE = 10  # 10 loops de 0.5s = 5 segundos

    while not stop_event.is_set():
        is_looking = tracker.is_focused()
        current_ratio = tracker.get_iris_ratio() # Valor exato da posição do olho
        
        # 1. Atualizar histórico
        gaze_history.append(current_ratio)
        if len(gaze_history) > HISTORY_SIZE:
            gaze_history.pop(0) # Remove o mais antigo

        # 2. Calcular se está "Vidrado" (Zoning Out)
        is_zoning_out = False
        if len(gaze_history) == HISTORY_SIZE:
            # Variação do olhar nos últimos 5s
            variation = max(gaze_history) - min(gaze_history)
            
            # Se a variação for minúscula (< 0.01), o olho não mexeu nem um milímetro
            if variation < 0.015: 
                is_zoning_out = True

        # --- LOGICA DE ESTADOS ---
        
        # Prioridade 1: Zoning Out (Olhar parado 5s)
        if is_zoning_out:
            if current_mood != "zoning":
                print("\n -> [Eye] ZONING OUT! (Olhar vidrado 5s).")
                # Usa 'side_eyes' ou 'thinking' para mostrar suspeita/dúvida
                robot.set_screen(image="side_eyes.jpeg") 
                robot.set_tilt(0) # Cabeça direita
                current_mood = "zoning"
            
            # Reset aos outros contadores para não conflituar
            count_focused = 0
            count_distracted = 0

        # Prioridade 2: Focado (Normal)
        elif is_looking:
            count_focused += 1
            count_distracted = 0
            if count_focused >= STABILITY_LIMIT:
                if current_mood != "normal":
                    print("\n -> [Eye] Focado! A ficar animado...")
                    robot.set_tilt(0)
                    if current_mood == "sad": # Só festeja se vier de triste
                        robot.set_screen(image="happy_eyes.jpeg")
                        time.sleep(2.0)
                    
                    robot.set_screen(image="normal.png")
                    current_mood = "normal"
                count_focused = STABILITY_LIMIT 

        # Prioridade 3: Distraído (Olhar para longe)
        else:
            count_distracted += 1
            count_focused = 0
            if count_distracted >= STABILITY_LIMIT:
                if current_mood != "sad":
                    print("\n -> [Eye] Distraído! A baixar cabeça...")
                    robot.set_tilt(15)
                    robot.set_screen(image="sad_eyes.jpeg") 
                    current_mood = "sad"
                count_distracted = STABILITY_LIMIT

        # Debug print
        state_txt = "ZONING" if is_zoning_out else ("FOCADO" if is_looking else "DISTRAIDO")
        print(f" -> Olho: {current_ratio:.3f} | Variação(5s): {max(gaze_history)-min(gaze_history):.3f} | Estado: {state_txt}   ", end='\r')

        time.sleep(0.5)
    
    print("\n -> [Thread] Vigilância terminada.")
    """
    Vigia os olhos e ccontrola a cabeça.
    Focado -> Cabeça ao centro (0) + Olhos Felizes -> Normais.
    Distraído -> Cabeça para baixo (15) + Olhos Tristes.
    """
    print(" -> [Thread] Vigilância iniciada (Com movimento de cabeça).")
    current_mood = "normal"
    
    # Define estado inicial (Olhar em frente, imagem normal)
    try:
        robot.set_screen(image="normal.png")
        robot.set_tilt(0) 
    except:
        print(" -> [Aviso] Falha ao definir estado inicial.")
    
    count_focused = 0
    count_distracted = 0
    STABILITY_LIMIT = 3 

    while not stop_event.is_set():
        is_looking = tracker.is_focused()
        
        # --- DEBUG PRINT ---
        status = "FOCADO" if is_looking else "DISTRAIDO"
        print(f" -> Detetado: {status} | Estado: {current_mood}   ", end='\r')

        if is_looking:
            count_focused += 1
            count_distracted = 0
        else:
            count_distracted += 1
            count_focused = 0

        try:
            # --- MUDANÇA PARA FOCADO (Levantar cabeça e celebrar) ---
            if count_focused >= STABILITY_LIMIT:
                if current_mood != "normal":
                    print("\n -> [Eye] Focado! A levantar a cabeça...")
                    
                    # 1. Levanta a cabeça para o centro
                    robot.set_tilt(0)
                    
                    # 2. Mostra olhos felizes
                    robot.set_screen(image="happy_eyes.jpeg")
                    
                    # 3. Mantém a felicidade por 2.5 segundos
                    time.sleep(2.5)
                    
                    # 4. Volta à expressão de estudo (Normal)
                    print(" -> [Eye] Modo estudo (Normal).")
                    robot.set_screen(image="normal.png")
                    
                    current_mood = "normal"
                
                count_focused = STABILITY_LIMIT 

            # --- MUDANÇA PARA DISTRAÍDO (Baixar cabeça e ficar triste) ---
            elif count_distracted >= STABILITY_LIMIT:
                if current_mood != "sad":
                    print("\n -> [Eye] Distraído! A baixar a cabeça...")
                    
                    # 1. Baixa a cabeça (para demonstrar tristeza)
                    # NOTA: Se ele olhar para CIMA em vez de baixo, muda 15 para -15
                    robot.set_tilt(15)
                    
                    # 2. Mostra olhos tristes
                    robot.set_screen(image="sad_eyes.jpeg") 
                    
                    current_mood = "sad"
                
                count_distracted = STABILITY_LIMIT

        except Exception as e:
            print(f"\n -> [Rede] Erro ligeiro: {e}")

        time.sleep(0.5)
    
    print("\n -> [Thread] Vigilância terminada.")
    """
    Vigia os olhos.
    Focado -> Imagem Normal (com celebração 'Happy' na transição).
    Distraído -> Imagem Triste.
    """
    print(" -> [Thread] Vigilância iniciada (Modo Happy/Sad).")
    current_mood = "normal"
    
    # Define estado inicial
    try:
        robot.set_screen(image="normal.png")
    except:
        print(" -> [Aviso] Falha ao definir ecrã inicial.")
    
    count_focused = 0
    count_distracted = 0
    # Aumentei um pouco a estabilidade para 3 (1.5s) para evitar "piscas" falsos
    STABILITY_LIMIT = 3 

    while not stop_event.is_set():
        is_looking = tracker.is_focused()
        
        # --- DEBUG PRINT ---
        status = "FOCADO" if is_looking else "DISTRAIDO"
        # Mostra o que ele vê e o estado atual
        print(f" -> Detetado: {status} | Estado: {current_mood}   ", end='\r')

        if is_looking:
            count_focused += 1
            count_distracted = 0
        else:
            count_distracted += 1
            count_focused = 0

        try:
            # --- MUDANÇA PARA FOCADO (Celebrar!) ---
            if count_focused >= STABILITY_LIMIT:
                if current_mood != "normal":
                    print("\n -> [Eye] Focado! A ficar animado...")
                    
                    # 1. Mostra olhos felizes
                    robot.set_screen(image="happy_eyes.jpeg")
                    
                    # 2. Mantém a felicidade por 2.5 segundos
                    time.sleep(2.5)
                    
                    # 3. Volta ao normal (Study Mode)
                    print(" -> [Eye] A voltar ao modo estudo (Normal).")
                    robot.set_screen(image="normal.png")
                    
                    current_mood = "normal"
                
                count_focused = STABILITY_LIMIT 

            # --- MUDANÇA PARA DISTRAÍDO (Ficar Triste) ---
            elif count_distracted >= STABILITY_LIMIT:
                if current_mood != "sad":
                    print("\n -> [Eye] Distraído! A ficar triste...")
                    robot.set_screen(image="sad_eyes.jpeg") 
                    current_mood = "sad"
                
                count_distracted = STABILITY_LIMIT

        except Exception as e:
            print(f"\n -> [Rede] Erro ligeiro: {e}")

        time.sleep(0.5)
    
    print("\n -> [Thread] Vigilância terminada.")
    """
    Watch eyes in background.
    If focused -> Normal Image.
    If distracted -> Sad Image.
    """
    print(" -> [Thread] Eye vigilance started (IMAGE MODE).")
    current_mood = "normal"
    
    # Set initial state
    try:
        robot.set_screen(image="normal.png")
    except:
        print(" -> [Warning] Failed to set initial screen.")
    
    count_focused = 0
    count_distracted = 0
    STABILITY_LIMIT = 2 

    while not stop_event.is_set():
        is_looking = tracker.is_focused()
        
        # --- DEBUG PRINT (Remove later if too noisy) ---
        status = "FOCUSED" if is_looking else "DISTRACTED"
        print(f" -> Detecting: {status} | Mood: {current_mood}", end='\r')
        # -----------------------------------------------

        if is_looking:
            count_focused += 1
            count_distracted = 0
        else:
            count_distracted += 1
            count_focused = 0

        try:
            # --- CHANGE TO FOCUSED ---
            if count_focused >= STABILITY_LIMIT:
                if current_mood != "normal":
                    print("\n -> [Eye] Focused. Switching to Normal Image.")
                    robot.set_screen(image="normal.png")
                    current_mood = "normal"
                count_focused = STABILITY_LIMIT 

            # --- CHANGE TO DISTRACTED ---
            elif count_distracted >= STABILITY_LIMIT:
                if current_mood != "sad":
                    print("\n -> [Eye] Distracted! Switching to Sad Image.")
                    robot.set_screen(image="sad_eyes.jpeg") 
                    current_mood = "sad"
                count_distracted = STABILITY_LIMIT

        except Exception as e:
            print(f"\n -> [Network] Minor error: {e}")

        time.sleep(0.5)
    
    print("\n -> [Thread] Vigilance ended.")
    """
    Vigia os olhos em segundo plano.
    Se estiver focado -> Imagem Normal.
    Se estiver distraído -> Imagem Triste.
    """
    print(" -> [Thread] Vigilância de olhos iniciada (MODO IMAGENS).")
    current_mood = "normal"
    
    # Define o estado inicial
    try:
        robot.set_screen(image="normal.png")
    except:
        print(" -> [Aviso] Falha ao definir ecrã inicial.")
    
    # Contadores para estabilizar a decisão (evitar pisca-pisca)
    count_focused = 0
    count_distracted = 0
    STABILITY_LIMIT = 2  # 1 segundo de confirmação antes de mudar

    while not stop_event.is_set():
        is_looking = tracker.is_focused()
        
        # Lógica de contagem
        if is_looking:
            count_focused += 1
            count_distracted = 0
        else:
            count_distracted += 1
            count_focused = 0

        try:
            # --- MUDANÇA PARA FOCADO ---
            if count_focused >= STABILITY_LIMIT:
                if current_mood != "normal":
                    print(" -> [Eye] Focado. Imagem Normal.")
                    # Apenas define a imagem, sem vídeos
                    robot.set_screen(image="normal.png")
                    current_mood = "normal"
                # Mantém o contador no limite para não crescer infinitamente
                count_focused = STABILITY_LIMIT 

            # --- MUDANÇA PARA DISTRAÍDO ---
            elif count_distracted >= STABILITY_LIMIT:
                if current_mood != "sad":
                    print(" -> [Eye] Distraído! Imagem Triste.")
                    # Define a imagem triste estática
                    # Confirma se o ficheiro no robô é .jpeg ou .png!
                    robot.set_screen(image="sad_eyes.jpeg") 
                    current_mood = "sad"
                count_distracted = STABILITY_LIMIT

        except Exception as e:
            print(f" -> [Rede] Erro ligeiro: {e}")

        # Verifica a cada 0.5s
        time.sleep(0.5)
    
    print(" -> [Thread] Vigilância terminada.")
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Erro: Falta IP.")
        sys.exit(1)

    print("--- A LIGAR AO ROBÔ (SÓ EYE TRACKING) ---")
    
    # 1. INICIALIZAR ROBÔ
    try:
        robot = ElmoV2API(sys.argv[1], debug=False)
        robot.enable_behavior("look_around", False)
        robot.enable_behavior("blush", False)
        time.sleep(0.5)
        robot.set_pan_torque(True)
        robot.set_tilt_torque(True)
        robot.set_pan(0) 
        robot.set_tilt(0)
    except Exception as e:
        print(f"Erro fatal ao ligar: {e}")
        sys.exit(1)

    # 2. INICIAR EYE TRACKER
    print(" -> A iniciar Webcam...")
    tracker = EyeTracker()
    tracker.start()
    
    stop_event = threading.Event()
    
    # 3. LANÇAR VIGILÂNCIA EM PARALELO
    attention_thread = threading.Thread(
        target=monitor_attention, 
        args=(robot, tracker, stop_event)
    )
    attention_thread.start()
    
    print("--- VIGILÂNCIA ATIVA ---")
    print("Pressiona CTRL+C para parar.")

    # 4. LOOP PRINCIPAL INFINITO
    # O programa fica aqui preso para sempre até o desligares
    try:
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n!!! A PARAR O ROBÔ !!!")
        
    finally:
        # Limpezas Finais
        print(" -> A desligar sistemas...")
        stop_event.set()        # Para a thread
        tracker.stop()          # Desliga a webcam
        attention_thread.join() # Espera thread fechar
        
        try:
            robot.set_pan_torque(False)
            robot.set_tilt_torque(False)
        except:
            pass
            
        print("--- SESSÃO TERMINADA ---")