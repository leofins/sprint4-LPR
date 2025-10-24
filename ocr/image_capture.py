# responsabilidade de processar a imagem: ele vai capturar o frame, desenhar o retângulo verde e o texto, 
# e depois retornar o frame modificado.

#!/usr/bin/env python3
"""
Módulo para captura de imagem da webcam, detecção de placas e integração com o motor OCR.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any
import time
import argparse

# Importa o motor OCR
from ocr.ocr_engine import OCREngine

class ImageCaptureProcessor:
    """Classe para capturar imagens, detectar placas e processá-las com OCR."""
    
    def __init__(self, camera_index: int = 0, ocr_engine: Optional[OCREngine] = None):
        """
        Inicializa o processador de captura de imagem.
        """
        self.camera_index = camera_index
        self.cap = None
        self.ocr_engine = ocr_engine if ocr_engine else OCREngine()
        
        cascade_path = 'haarcascade_russian_plate_number.xml'
        if not cv2.os.path.exists(cascade_path):
             cascade_path = cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'

        self.plate_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.plate_cascade.empty():
            print(f"ERRO: Não foi possível carregar o classificador de placas em: {cascade_path}")
            raise FileNotFoundError("Classificador de placas não encontrado.")
        
        print(f"ImageCaptureProcessor inicializado para câmera {self.camera_index}.")
        self._initialize_camera()

    def _initialize_camera(self) -> bool:
        """
        Inicializa a câmera.
        """
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print(f"ERRO: Não foi possível abrir a câmera com índice {self.camera_index}.")
                return False
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            print(f"Câmera {self.camera_index} inicializada com sucesso.")
        return True

    def _release_camera(self):
        """
        Libera os recursos da câmera.
        """
        if self.cap and self.cap.isOpened():
            self.cap.release()
            print(f"Câmera {self.camera_index} liberada.")
        self.cap = None

    def capture_and_process_frame(self) -> Tuple[Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """
        Captura um frame, detecta placas, desenha na imagem e realiza OCR.
        """
        if not self.cap or not self.cap.isOpened():
            if not self._initialize_camera():
                return None, None

        ret, frame = self.cap.read()
        if not ret:
            print("ERRO: Não foi possível ler o frame da câmera.")
            return None, None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # Removi o 'maxSize' para detectar placas grandes (de perto)
        # e diminui 'minNeighbors' para deixar a detecção mais flexível.
        plates = self.plate_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=4,     # <-- Alterado de 5 para 4
            minSize=(50, 20)
            # maxSize foi removido
        )

        detected_plate_info = None
        max_confidence = 0.0
        best_bbox = None

        for (x, y, w, h) in plates:
            plate_roi = frame[y:y+h, x:x+w]
            ocr_result = self.ocr_engine.extract_plate_info(plate_roi)
            
            if ocr_result and ocr_result["confianca"] > max_confidence:
                max_confidence = ocr_result["confianca"]
                detected_plate_info = {
                    "placa": ocr_result["placa"],
                    "confianca": ocr_result["confianca"],
                }
                best_bbox = (x, y, w, h)
        
        if best_bbox:
            x, y, w, h = best_bbox
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            if detected_plate_info:
                text = f"{detected_plate_info['placa']} ({detected_plate_info['confianca']:.2f})"
                cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return frame, detected_plate_info

    def __del__(self):
        """
        Garante que a câmera seja liberada quando o objeto for destruído.
        """
        self._release_camera()