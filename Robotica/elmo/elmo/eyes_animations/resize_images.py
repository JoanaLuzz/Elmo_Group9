import cv2
import os

# Pares de ficheiros: (Video Fonte, Imagem para corrigir)
# Certifica-te que os nomes estão iguais aos que tens na pasta
files_to_fix = [
    ("sad_eyes.mp4", "sad_eyes.jpeg"),
    ("angry_eyes.mp4", "angry_eyes.jpeg"),
    # Adiciona os outros pares se tiveres (ex: happy, side)
    # ("happy_eyes.mp4", "happy_eyes.jpeg"),
    # ("side_eyes.mp4", "side_eyes.jpeg"),
]

print("--- A REDIMENSIONAR IMAGENS ---")

for video_file, image_file in files_to_fix:
    # 1. Verificar se ficheiros existem
    if not os.path.exists(video_file) or not os.path.exists(image_file):
        print(f"ERRO: Ficheiro não encontrado ({video_file} ou {image_file})")
        continue

    # 2. Ler as dimensões do vídeo
    cap = cv2.VideoCapture(video_file)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    if width == 0 or height == 0:
        print(f"ERRO: Não consegui ler dimensões do vídeo {video_file}")
        continue

    print(f"Vídeo {video_file}: {width}x{height} pixels")

    # 3. Ler a imagem
    img = cv2.imread(image_file)
    if img is None:
        print(f"ERRO: Não consegui abrir a imagem {image_file}")
        continue
    
    old_h, old_w, _ = img.shape
    print(f"  -> Imagem original: {old_w}x{old_h}")

    # 4. Redimensionar a imagem se for diferente
    if (old_w != width) or (old_h != height):
        # Resize forçado para igualar o vídeo
        resized_img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
        
        # Guardar por cima da original (ou muda o nome se preferires)
        cv2.imwrite(image_file, resized_img)
        print(f"  -> SUCESSO: {image_file} redimensionada para {width}x{height}!")
    else:
        print(f"  -> OK: A imagem já tem o tamanho certo.")

print("--- CONCLUÍDO ---")