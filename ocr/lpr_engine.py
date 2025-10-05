#!/usr/bin/env python3
"""
LPR Engine: pipeline moderno para detecção e reconhecimento de placas.
- Tenta usar Ultralytics YOLO para detecção de placa e EasyOCR para reconhecimento.
- Se não estiverem disponíveis, faz fallback para Haar cascade + pytesseract.

Interface:
- class LPREngine:
    - extract_plate_from_image(image) -> (plate_text, confidence, bbox, plate_image)

Observação: este módulo tenta importar bibliotecas opcionais. Se você quiser usar o pipeline completo,
instale 'ultralytics' e 'easyocr' no seu ambiente.
"""

from typing import Optional, Tuple, Any
import numpy as np
import cv2

#!/usr/bin/env python3
"""
LPR Engine: pipeline moderno para detecção e reconhecimento de placas.
- Tenta usar Ultralytics YOLO para detecção de placa e EasyOCR para reconhecimento.
- Se não estiverem disponíveis, faz fallback para Haar cascade + pytesseract.

Interface:
- class LPREngine:
    - extract_plate_from_image(image) -> (plate_text, confidence, bbox, plate_image)

Observação: este módulo tenta importar bibliotecas opcionais. Se você quiser usar o pipeline completo,
instale 'ultralytics' e 'easyocr' no seu ambiente.
"""

from typing import Optional, Tuple
import numpy as np
import cv2

# Tentar importar Ultralytics YOLO (detecção moderna)
try:
    from ultralytics import YOLO
    _HAS_YOLO = True
except Exception:
    _HAS_YOLO = False

# Tentar importar EasyOCR (reconhecimento moderno)
try:
    import easyocr
    _HAS_EASYOCR = True
except Exception:
    _HAS_EASYOCR = False

# Fallbacks
from ocr.ocr_engine import OCREngine


class LPREngine:
    def __init__(self, yolo_model_path: Optional[str] = None, reader_langs: Optional[list] = None, try_download: bool = False, cascade_params: dict = None):
        """Inicializa o LPR engine.

        Args:
            yolo_model_path: caminho para pesos YOLO (.pt). Se None, tentamos localizar em ./models/*.pt
            reader_langs: línguas para easyocr
            try_download: se True e ultralytics instalado, tenta usar modelo yolov8n (pode baixar pesos)
            cascade_params: dict com keys para detectMultiScale (scaleFactor, minNeighbors, minSize, maxSize)
        """
        # Tentar achar modelo YOLO automaticamente se não passado
        if not yolo_model_path:
            import glob, os
            candidates = glob.glob(os.path.join(os.path.dirname(__file__), '..', 'models', '*.pt'))
            candidates = [c for c in candidates if os.path.isfile(c)]
            yolo_model_path = candidates[0] if candidates else None

        self.use_yolo = _HAS_YOLO and bool(yolo_model_path or try_download)
        self.yolo = None
        if _HAS_YOLO and yolo_model_path:
            try:
                self.yolo = YOLO(yolo_model_path)
            except Exception as e:
                print(f"Falha ao carregar YOLO weights '{yolo_model_path}': {e}")
                self.yolo = None
                self.use_yolo = False
        elif _HAS_YOLO and try_download:
            try:
                # Tentar usar um modelo pequeno padrão (pode baixar)
                self.yolo = YOLO('yolov8n.pt')
            except Exception as e:
                print(f"Não foi possível baixar/usar yolov8n.pt automaticamente: {e}")
                self.yolo = None
                self.use_yolo = False

        self.use_easyocr = _HAS_EASYOCR
        self.reader = None
        if self.use_easyocr:
            langs = reader_langs if reader_langs else ['en']
            try:
                self.reader = easyocr.Reader(langs, gpu=False)
            except Exception as e:
                print(f"EasyOCR inicialização falhou: {e}")
                self.reader = None
                self.use_easyocr = False

        # Fallback OCR
        self.fallback_ocr = OCREngine()

        # Cascade fallback detector
        self.cascade_params = cascade_params or {}
        self.plate_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml')
        if self.plate_cascade.empty():
            print("Aviso: Haar cascade de placas não carregado; detecção por cascade pode falhar.")

    def detect_plate_bboxes(self, image: np.ndarray):
        h, w = image.shape[:2]
        bboxes = []
        if self.use_yolo and self.yolo:
            try:
                results = self.yolo(image)
                for r in results:
                    if hasattr(r, 'boxes'):
                        for box in r.boxes:
                            xyxy = box.xyxy[0].cpu().numpy()
                            x1, y1, x2, y2 = xyxy.astype(int)
                            bx = max(0, x1); by = max(0, y1)
                            bw = min(w, x2) - bx; bh = min(h, y2) - by
                            if bw > 10 and bh > 10:
                                bboxes.append((bx, by, bw, bh))
            except Exception as e:
                print(f"YOLO detection failed: {e}")
                self.use_yolo = False

        if not bboxes:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            gray = cv2.equalizeHist(gray)
            # Use cascade params if fornecidos
            cp = self.cascade_params
            scaleFactor = cp.get('scaleFactor', 1.1) if isinstance(cp, dict) else 1.1
            minNeighbors = cp.get('minNeighbors', 4) if isinstance(cp, dict) else 4
            minSize = tuple(cp.get('minSize', (30, 15))) if isinstance(cp, dict) else (30, 15)
            maxSize = tuple(cp.get('maxSize', (400, 200))) if isinstance(cp, dict) else (400, 200)
            plates = self.plate_cascade.detectMultiScale(gray, scaleFactor=scaleFactor, minNeighbors=minNeighbors, minSize=minSize, maxSize=maxSize)
            for (x, y, w, h) in plates:
                bboxes.append((int(x), int(y), int(w), int(h)))

        return bboxes

    def recognize_text(self, plate_image: np.ndarray):
        if self.use_easyocr and self.reader:
            try:
                results = self.reader.readtext(plate_image)
                if results:
                    best = max(results, key=lambda r: r[2])
                    txt = best[1]
                    conf_raw = best[2]
                    try:
                        conf = float(conf_raw)
                        if conf > 1.0:
                            conf = conf / 100.0
                    except Exception:
                        conf = 0.0
                    return ''.join(filter(str.isalnum, txt)).upper(), float(conf)
            except Exception as e:
                print(f"EasyOCR failed: {e}")
                self.use_easyocr = False

        text, conf = self.fallback_ocr.extract_plate_text(plate_image)
        return text, conf

    def extract_plate_from_image(self, image: np.ndarray):
        bboxes = self.detect_plate_bboxes(image)
        best = (None, 0.0, None, None)
        for (x, y, w, h) in bboxes:
            roi = image[y:y+h, x:x+w]
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
            roi_resized = cv2.resize(roi_gray, (0,0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            roi_eq = cv2.equalizeHist(roi_resized)
            plate_text, conf = self.recognize_text(roi_eq)
            if plate_text and conf > best[1]:
                best = (plate_text, conf, (x,y,w,h), roi)
        return best


if __name__ == '__main__':
    print('LPREngine module loaded. No external models? YOLO:', _HAS_YOLO, 'EasyOCR:', _HAS_EASYOCR)
