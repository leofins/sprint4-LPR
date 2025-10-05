#!/usr/bin/env python3
"""
Módulo para captura de imagem da webcam, detecção de placas e integração com o motor OCR.
"""

from __future__ import annotations

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING
import time
import os

# Importa o motor OCR (LPREngine se disponível). OCREngine é importado apenas para type checking
try:
    from ocr.lpr_engine import LPREngine
    _HAS_LPR = True
except Exception:
    _HAS_LPR = False

if TYPE_CHECKING:
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
        # Prefer LPREngine if disponível (detecção moderna + EasyOCR)
        if _HAS_LPR and (ocr_engine is None):
            try:
                self.lpr = LPREngine()
                self.ocr_engine = None
            except Exception:
                self.lpr = None
                self.ocr_engine = ocr_engine if ocr_engine else OCREngine()
        else:
            self.lpr = None
            self.ocr_engine = ocr_engine if ocr_engine else OCREngine()

        # Mantemos o cascade como fallback de detecção
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
            print("Erro ao capturar frame da câmera.")
            return None

        # --- ADICIONE ESTAS LINHAS PARA VISUALIZAÇÃO ---
        cv2.imshow("Webcam Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            # Pressione \'q\' para fechar a janela e sair (opcional, para testes)
            return None

        if not ret:
            print("ERRO: Não foi possível ler o frame da câmera.")
            return None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)  # Melhorar contraste

        # Detecta placas na imagem
        plates = self.plate_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 20),  # Tamanho mínimo da placa
            maxSize=(200, 80)  # Tamanho máximo da placa
        )

        # Informativo: quantas possíveis placas o classificador encontrou
        print(f"Detectadas {len(plates)} possíveis placas pelo cascade.")

        detected_plate_info = None
        max_confidence = 0.0

        # If LPREngine present, use it as higher-level pipeline
        if getattr(self, 'lpr', None):
            plate_text, conf, bbox, plate_img = self.lpr.extract_plate_from_image(frame)
            if plate_text and conf > 0:
                x, y, w, h = bbox
                detected_plate_info = {
                    "placa": plate_text,
                    "confianca": conf,
                    "roi": (x, y, w, h),
                    "image": plate_img
                }
                # Save ROI for debug
                try:
                    debug_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp_debug')
                    os.makedirs(debug_dir, exist_ok=True)
                    ts = int(time.time() * 1000)
                    debug_path = os.path.join(debug_dir, f"plate_roi_{ts}_lpr.png")
                    cv2.imwrite(debug_path, plate_img)
                    print(f"LPR ROI salva: {debug_path} (from LPR pipeline)")
                except Exception as e:
                    print(f"Não foi possível salvar LPR ROI: {e}")

        else:
            for (x, y, w, h) in plates:
                plate_roi = frame[y:y + h, x:x + w]
                try:
                    debug_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp_debug')
                    os.makedirs(debug_dir, exist_ok=True)
                    ts = int(time.time() * 1000)
                    debug_path = os.path.join(debug_dir, f"plate_roi_{ts}_{x}_{y}.png")
                    cv2.imwrite(debug_path, plate_roi)
                    print(f"ROI salva para depuração: {debug_path} (w={w}, h={h})")
                except Exception as e:
                    print(f"Não foi possível salvar ROI para depuração: {e}")

                plate_text, confidence = self.ocr_engine.extract_plate_text(plate_roi)

                if plate_text and confidence > max_confidence:
                    max_confidence = confidence
                    detected_plate_info = {
                        "placa": plate_text,
                        "confianca": confidence,
                        "roi": (x, y, w, h),
                        "image": plate_roi
                    }

        # Opcional: Mostrar o frame com as detecções (para depuração)
        # if detected_plate_info:
        #     x, y, w, h = detected_plate_info["roi"]
        #     cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        #     cv2.putText(frame, detected_plate_info["placa"], (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        # cv2.imshow("Frame", frame)
        # cv2.waitKey(1)

        return detected_plate_info

    def __del__(self):
        """
        Garante que a câmera seja liberada quando o objeto for destruído.
        """
        self._release_camera()


if __name__ == "__main__":
    # Exemplo de uso:
    # Certifique-se de ter uma webcam conectada e o Tesseract instalado.

    try:
        # Inicializa o processador de imagem
        processor = ImageCaptureProcessor(camera_index=0)  # Use 0 para a câmera padrão

        print("Pressione 'q' para sair.")

        while True:
            plate_info = processor.capture_and_process_frame()

            if plate_info:
                print(f"Detectado: Placa=\"{plate_info['placa']}\", Confiança={plate_info['confianca']:.2f}")
                # Você pode salvar a imagem da placa para depuração
                # cv2.imwrite(f"detected_plate_{plate_info["placa"]}.png", plate_info["image"])
            else:
                print("Nenhuma placa detectada.")

            # Pequeno atraso para evitar sobrecarga da CPU
            time.sleep(0.1)

            # Para sair do loop, se estiver usando cv2.imshow
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

    except FileNotFoundError as e:
        print(f"Erro de arquivo: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        # Garante que a câmera seja liberada
        if 'processor' in locals() and processor.cap and processor.cap.isOpened():
            processor._release_camera()
        cv2.destroyAllWindows()  # Fecha janelas do OpenCV, se houver