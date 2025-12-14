import sys
import time
import threading
from ElmoV2API import ElmoV2API
# IMPORTANTE: NÃO IMPORTAR O POMODORO
from eye_tracker import EyeTracker

def monitor_attention(robot, tracker, stop_event):
    """
    Vigia os olhos em segundo plano.
    Se estiver focado -> Normal.
    Se estiver distraído -> Triste (Sad Eyes).
    """
    print(" -> [Thread] Vigilância de olhos iniciada.")
    current_mood = "normal"
    
    # Tenta definir estado inicial
    try:
        robot.set_screen(image="normal.png")
    except:
        print(" -> [Aviso] Falha ao definir ecrã inicial.")
    
    # Contadores para estabilizar a decisão (evitar pisca-pisca)
    count_focused = 0
    count_distracted = 0
    STABILITY_LIMIT = 2 # 1 segundo (2 ciclos de 0.5s)

    while not stop_event.is_set():
        is_looking = tracker.is_focused()
        
        # Lógica de estabilização
        if is_looking:
            count_focused += 1
            count_distracted = 0
        else:
            count_distracted += 1
            count_focused = 0

        try:
            # Lógica de Mudança
            if count_focused >= STABILITY_LIMIT:
                if current_mood != "normal":
                    print(" -> [Eye] Focado. Normal.")
                    robot.set_screen(image="normal.png")
                    current_mood = "normal"
                count_focused = STABILITY_LIMIT # Mantém no máximo

            elif count_distracted >= STABILITY_LIMIT:
                if current_mood != "sad":
                    print(" -> [Eye] Distraído! Sad Eyes.")
                    # Tenta mostrar video
                    robot.set_screen(video="sad_eyes.mp4") 
                    current_mood = "sad"
                count_distracted = STABILITY_LIMIT # Mantém no máximo

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
        stop_event.set()        # Pára a thread
        tracker.stop()          # Desliga a webcam
        attention_thread.join() # Espera thread fechar
        
        try:
            robot.set_pan_torque(False)
            robot.set_tilt_torque(False)
        except:
            pass
            
        print("--- SESSÃO TERMINADA ---")