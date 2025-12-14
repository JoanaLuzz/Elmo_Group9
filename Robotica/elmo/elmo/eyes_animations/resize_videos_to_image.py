import cv2
import os

# Pares de ficheiros: (Video para aumentar, Imagem de referência)
# O script vai ler o tamanho da IMAGEM e aplicar ao VÍDEO.
files_to_fix = [
    ("sad_eyes.mp4", "sad_eyes.jpeg"),
    ("sad_eyes_to_normal.mp4", "sad_eyes.jpeg"), # Usa a mesma imagem de referência
    ("angry_eyes.mp4", "angry_eyes.jpeg"),
    ("angry_eyes_to_normal.mp4", "angry_eyes.jpeg"),
    ("happy_eyes.mp4", "happy_eyes.jpeg"),
    ("happy_eyes_to_normal.mp4", "happy_eyes.jpeg"),
    ("side_eyes.mp4", "side_eyes.jpeg"),
    ("side_eyes_to_normal.mp4", "side_eyes.jpeg"),
]

print("--- A REDIMENSIONAR VÍDEOS (UPSCALING) ---")

for video_file, image_file in files_to_fix:
    # 1. Verificar ficheiros
    if not os.path.exists(video_file) or not os.path.exists(image_file):
        print(f"Saltar (Ficheiro em falta): {video_file} ou {image_file}")
        continue

    # 2. Ler o tamanho ALVO da Imagem
    img = cv2.imread(image_file)
    if img is None:
        continue
    target_h, target_w, _ = img.shape
    print(f"Alvo (Imagem): {target_w}x{target_h} -> A aplicar ao vídeo {video_file}...")

    # 3. Preparar o Vídeo
    cap = cv2.VideoCapture(video_file)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Criar nome para o novo vídeo (ex: sad_eyes_big.mp4)
    # Assim não apaga o original se correr mal
    new_video_name = video_file.replace(".mp4", "_big.mp4")
    
    # Codec para MP4
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(new_video_name, fourcc, fps, (target_w, target_h))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Redimensionar frame para o tamanho da imagem
        resized_frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        out.write(resized_frame)

    cap.release()
    out.release()
    print(f" -> Criado: {new_video_name}")

print("--- CONCLUÍDO ---")