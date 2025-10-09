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
        
        Args:
            camera_index: Índice da câmera a ser utilizada (0 para a câmera padrão).
            ocr_engine: Instância do motor OCR. Se None, uma nova será criada.
        """
        self.camera_index = camera_index
        self.cap = None
        self.ocr_engine = ocr_engine if ocr_engine else OCREngine()
        self.plate_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
        )
        if self.plate_cascade.empty():
            print("ERRO: Não foi possível carregar o classificador de placas.")
            print("Verifique se 'haarcascade_russian_plate_number.xml' está no caminho correto.")
            raise FileNotFoundError("Classificador de placas não encontrado.")
        
        print(f"ImageCaptureProcessor inicializado para câmera {self.camera_index}.")

    def _initialize_camera(self) -> bool:
        """
        Inicializa a câmera.
        
        Returns:
            True se a câmera foi inicializada com sucesso, False caso contrário.
        """
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print(f"ERRO: Não foi possível abrir a câmera com índice {self.camera_index}.")
                return False
            
            # Configurações da câmera (opcional, pode variar)
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

    def capture_and_process_frame(self) -> Optional[Dict[str, Any]]:
        """
        Captura um frame, detecta placas e realiza OCR.
        
        Returns:
            Dicionário com a placa detectada, confiança e imagem da placa, 
            ou None se nenhuma placa for detectada.
        """
        if not self._initialize_camera():
            return None

        ret, frame = self.cap.read()
        if not ret:
            print("ERRO: Não foi possível ler o frame da câmera.")
            return None

        # Converte para escala de cinza para detecção de placas
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray) # Melhorar contraste

        # Detecta placas na imagem
        plates = self.plate_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(50, 20), # Tamanho mínimo da placa
            maxSize=(200, 80)  # Tamanho máximo da placa
        )

        detected_plate_info = None
        max_confidence = 0.0
        best_bbox = None

        for (x, y, w, h) in plates:
            # Recorta a região da placa
            plate_roi = frame[y:y+h, x:x+w]
            
            # Realiza OCR na região da placa usando o novo método extract_plate_info
            ocr_result = self.ocr_engine.extract_plate_info(plate_roi)
            
            if ocr_result and ocr_result["confianca"] > max_confidence:
                max_confidence = ocr_result["confianca"]
                detected_plate_info = {
                    "placa": ocr_result["placa"],
                    "confianca": ocr_result["confianca"],
                    "roi": (x, y, w, h), # Região de interesse da placa no frame original
                    "image": plate_roi # Imagem recortada da placa
                }
                best_bbox = (x, y, w, h)
        
        # Desenha o contorno verde na placa detectada (se houver)
        if best_bbox:
            x, y, w, h = best_bbox
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2) # Contorno verde
            if detected_plate_info:
                text_to_display = f"{detected_plate_info['placa']} ({detected_plate_info['confianca']:.2f})"
                cv2.putText(frame, text_to_display, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Exibe o frame com as detecções (ou sem, se nada for detectado)
        cv2.imshow("Webcam Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # Permite sair pressionando 'q'
            self._release_camera()
            cv2.destroyAllWindows()
            return None # Indica que o loop deve parar

        return detected_plate_info

    def __del__(self):
        """
        Garante que a câmera seja liberada quando o objeto for destruído.
        """
        self._release_camera()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processador de Captura de Imagem e OCR de Placas.")
    parser.add_argument("--camera", type=int, default=0, help="Índice da câmera a ser utilizada (ex: 0, 1).")
    args = parser.parse_args()

    try:
        # Inicializa o processador de imagem
        processor = ImageCaptureProcessor(camera_index=args.camera)
        
        print("Pressione 'q' na janela 'Webcam Feed' para sair.")
        
        while True:
            plate_info = processor.capture_and_process_frame()
            
            if plate_info:
                print(f"Detectado: Placa={plate_info['placa']}, Confiança={plate_info['confianca']:.2f}")
            else:
                print("Nenhuma placa detectada ou confiança baixa.")
            
            # Pequeno atraso para evitar sobrecarga da CPU
            time.sleep(0.05) # Reduzido para 0.05s para maior responsividade
                
    except FileNotFoundError as e:
        print(f"Erro de arquivo: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        # Garante que a câmera seja liberada e janelas fechadas ao sair
        if 'processor' in locals():
            processor._release_camera()
        cv2.destroyAllWindows() # Fecha janelas do OpenCV, se houver



