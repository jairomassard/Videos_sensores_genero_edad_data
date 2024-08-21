
import sys
import signal
import time
from datetime import datetime, timedelta
import os
import subprocess
import win32file, pywintypes
import json
import cv2
import numpy as np
import serial

running = True  # Asegúrate de que esta línea esté al inicio, después de los imports

# Define las rutas absolutas a las carpetas de Videos, Reportes, Capturas y modelos de Reconocimiento Facial
ruta_base = 'C:/Proyecto_Sensores_Estanterias/Programa_Sensores'
ruta_base2 = 'C:/Proyecto_Sensores_Estanterias/ProyectoSensores'
ruta_videos = os.path.join(ruta_base, 'Videos')
ruta_reportes = os.path.join(ruta_base, 'Reportes')
ruta_capturas = os.path.join(ruta_base, 'Capturas')
ruta_modelos = os.path.join(ruta_base2, 'Modelos')
ruta_assets = os.path.join(ruta_base2, 'assets')
canal_camara = 0

# Asegúrate de que las carpetas existan
os.makedirs(ruta_videos, exist_ok=True)
os.makedirs(ruta_reportes, exist_ok=True)
os.makedirs(ruta_capturas, exist_ok=True)
os.makedirs(ruta_modelos, exist_ok=True)
os.makedirs(ruta_assets, exist_ok=True)

# Diccionario para mapear códigos a nombres de archivo de video
videos = {
    "1A": {"archivo": "video1.mp4", "duracion": 15},
    "1B": {"archivo": "video2.mp4", "duracion": 15},
    "1C": {"archivo": "video3.mp4", "duracion": 14},
    "1D": {"archivo": "video4.mp4", "duracion": 15},
    "NULL": {"archivo": "Video_pantalla_Negra.mp4", "duracion": 1200},
}


# Configura el puerto serial. Reemplaza 'COM4' con tu puerto correcto.
ser = serial.Serial('COM4', 9600, timeout=1)
time.sleep(2)  # Espera para la inicialización del puerto serial

# Funciones de detección de rostro, género y edad
def highlightFace(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv2.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)

    net.setInput(blob)
    detections = net.forward()
    faceBoxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            faceBoxes.append([x1, y1, x2, y2])
            cv2.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight / 150)), 8)
    return frameOpencvDnn, faceBoxes

def analizar_genero_edad(image_path):
    faceProto = os.path.join(ruta_assets, 'opencv_face_detector.pbtxt')
    faceModel = os.path.join(ruta_assets, 'opencv_face_detector_uint8.pb')
    ageProto = os.path.join(ruta_assets, 'age_deploy.prototxt')
    ageModel = os.path.join(ruta_assets, 'age_net.caffemodel')
    genderProto = os.path.join(ruta_assets, 'gender_deploy.prototxt')
    genderModel = os.path.join(ruta_assets, 'gender_net.caffemodel')

    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
    ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
    genderList = ['Male', 'Female']

    faceNet = cv2.dnn.readNet(faceModel, faceProto)
    ageNet = cv2.dnn.readNet(ageModel, ageProto)
    genderNet = cv2.dnn.readNet(genderModel, genderProto)

    image = cv2.imread(image_path)
    resultImg, faceBoxes = highlightFace(faceNet, image)
    if not faceBoxes:
        print("No face detected")
        return "Desconocido", "Desconocido"

    for faceBox in faceBoxes:
        face = image[max(0,faceBox[1]-20):
                     min(faceBox[3]+20,image.shape[0]-1),
                     max(0,faceBox[0]-20):
                     min(faceBox[2]+20, image.shape[1]-1)]

        blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
        genderNet.setInput(blob)
        genderPreds = genderNet.forward()
        gender = genderList[genderPreds[0].argmax()]

        ageNet.setInput(blob)
        agePreds = ageNet.forward()
        age = ageList[agePreds[0].argmax()]

        return gender, age

# Función para capturar imagen
def capturar_imagen():
    cam = cv2.VideoCapture(canal_camara)
    ret, frame = cam.read()
    if ret:
        filepath = os.path.join(ruta_capturas, "captura.jpg")
        cv2.imwrite(filepath, frame)
        cam.release()
        return filepath
    else:
        print("Error al capturar la imagen")
        return None

# Función para registrar en archivo CSV
def registrar_codigo(codigo, genero, rango_edad):
    archivo_csv = os.path.join(ruta_reportes, "estadisticas_codigos.csv")
    with open(archivo_csv, "a") as archivo:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        archivo.write(f"{fecha},{codigo},{genero},{rango_edad}\n")

# Configura las opciones de MPV
def set_mpv_options():
    send_command_to_mpv({"command": ["set_property", "fullscreen", True]})
    send_command_to_mpv({"command": ["set_property", "border", False]})
    send_command_to_mpv({"command": ["set_property", "ontop", True]})
# Función para enviar comandos a MPV
def send_command_to_mpv(command):
    try:
        handle = win32file.CreateFile(
            r'\\.\pipe\mpvsocket',
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )
        command_json = json.dumps(command) + "\n"
        win32file.WriteFile(handle, command_json.encode('utf-8'))
        win32file.CloseHandle(handle)
    except pywintypes.error as e:
        print(f"Error al enviar comando a MPV: {e}")


ultimo_cambio = datetime.now()

# Función para reproducir video ajustada para manejar la transición suave
# Función para reproducir video con MPV
def reproducir_video(codigo):
    global ultimo_cambio
    video_info = videos.get(codigo)
    if video_info:
        ruta_completa_video = os.path.join(ruta_videos, video_info["archivo"]).replace("\\", "/")
        
        # Carga el video especificado
        command_load = {"command": ["loadfile", ruta_completa_video, "replace"]}
        send_command_to_mpv(command_load)
        
        # Si el video a reproducir es el de pantalla negra, establece la propiedad de loop
        if codigo == "NULL":
            command_loop = {"command": ["set_property", "loop-file", "inf"]}
            send_command_to_mpv(command_loop)
        else:
            # Para cualquier otro video, asegura que la propiedad de loop esté desactivada
            command_no_loop = {"command": ["set_property", "loop-file", "no"]}
            send_command_to_mpv(command_no_loop)

        ultimo_cambio = datetime.now() + timedelta(seconds=video_info["duracion"])
        # Aplica las opciones de configuración de MPV
        set_mpv_options()

# Función para manejar la señal de interrupción y cerrar MPV antes de salir
def signal_handler(sig, frame):
    global running
    print('Cerrando MPV y terminando el programa...')
    send_command_to_mpv({"command": ["quit"]})
    ser.close()
    running = False

# Función principal ajustada para manejar adecuadamente los códigos en el buffer y la transición de videos
def main():
    global ultimo_cambio, running
    # Registra el manejador de señales para SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    codigo_actual = "NULL"
    reproducir_video(codigo_actual)
    video_en_reproduccion = codigo_actual
    duracion_actual = videos[codigo_actual]["duracion"]

    while running:
        if ser.in_waiting > 0:
            codigo_nuevo = ser.readline().decode('utf-8').rstrip()
            ser.reset_input_buffer()

            if codigo_nuevo != video_en_reproduccion:
                if codigo_nuevo in videos:
                    print(f"Sensor canal {codigo_nuevo} detectó obstáculo.")
                    if codigo_nuevo != "NULL":
                        filepath = capturar_imagen()
                        if filepath:
                            genero, rango_edad = analizar_genero_edad(filepath)
                            print(f"Género: {genero}, Rango de edad: {rango_edad}")
                            registrar_codigo(codigo_nuevo, genero, rango_edad)
                    reproducir_video(codigo_nuevo)
                    video_en_reproduccion = codigo_nuevo
                    codigo_actual = codigo_nuevo
                    duracion_actual = videos[codigo_nuevo]["duracion"]
                    ultimo_cambio = datetime.now()
                else:
                    print("Código desconocido recibido.")
        else:
            if datetime.now() - ultimo_cambio >= timedelta(seconds=duracion_actual) and video_en_reproduccion != "NULL":
                reproducir_video("NULL")
                video_en_reproduccion = "NULL"
                codigo_actual = "NULL"
                duracion_actual = videos["NULL"]["duracion"]
                ultimo_cambio = datetime.now()

        time.sleep(1)

    # Este mensaje se imprimirá después de salir del bucle while
    print("Programa terminado correctamente.")

if __name__ == "__main__":
    main()


