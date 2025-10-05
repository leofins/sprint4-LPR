#!/usr/bin/env python3
"""
Módulo para realizar OCR (Optical Character Recognition) em imagens de placas.
Utiliza a biblioteca Tesseract para extrair texto da imagem.
"""

import pytesseract
import cv2
import numpy as np
from typing import Optional, Tuple


class OCREngine:
    """Classe para encapsular a funcionalidade de OCR."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Inicializa o motor OCR.

        Args:
            tesseract_cmd: Caminho para o executável do Tesseract. Se None,
                           pytesseract tentará encontrá-lo automaticamente.
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Verifica se o Tesseract está configurado corretamente
        try:
            pytesseract.get_tesseract_version()
            print("Tesseract OCR Engine inicializado com sucesso.")
        except pytesseract.TesseractNotFoundError:
            print("ERRO: Tesseract não encontrado ou não configurado no PATH.")
            print("Por favor, instale o Tesseract e/ou configure a variável de ambiente TESSERACT_CMD.")
            raise

    def extract_plate_text(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Extrai o texto da placa de uma imagem usando OCR.

        Args:
            image: Imagem da placa (formato OpenCV - numpy array).

        Returns:
            Uma tupla contendo o texto da placa extraído e a confiança média.
        """
        if image is None or image.size == 0:
            return None, 0.0

        # Pré-processamento adicional para OCR (opcional, pode ser ajustado)
        # Converter para escala de cinza se ainda não estiver
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = image

        # Aumentar contraste e nitidez (ex: usando CLAHE ou equalização de histograma)
        # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        # enhanced_image = clahe.apply(gray_image)
        enhanced_image = cv2.equalizeHist(gray_image)

        # Binarização para destacar caracteres
        _, binary_image = cv2.threshold(enhanced_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Remover ruído (opcional)
        # kernel = np.ones((1,1), np.uint8)
        # denoised_image = cv2.erode(binary_image, kernel, iterations=1)
        # denoised_image = cv2.dilate(denoised_image, kernel, iterations=1)
        denoised_image = cv2.medianBlur(binary_image, 3)

        # Tentativa 1: PSM 8 (uma única palavra) — bom para placas pequenas
        base_config = r'--oem 3 -l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        custom_config_psm8 = base_config + ' --psm 8'

        # Extrai o texto e os dados detalhados (incluindo confiança)
        data = pytesseract.image_to_data(denoised_image, config=custom_config_psm8, output_type=pytesseract.Output.DICT)

        # Se não obteve resultados razoáveis, tenta PSM 7 (uma linha)
        confidences = []
        text = ""

        # Coleta os resultados iniciais
        for i in range(len(data["text"])):
            char = data["text"][i].strip()
            conf_raw = data["conf"][i]
            try:
                conf = int(conf_raw)
            except Exception:
                # Às vezes o Tesseract retorna '-1' ou strings; ignorar valores inválidos
                try:
                    conf = int(float(conf_raw))
                except Exception:
                    conf = -1

            if char and conf > 0:
                text += char
                confidences.append(conf)

        if not confidences:
            # Tenta PSM 7 (uma linha) como fallback
            custom_config_psm7 = base_config + ' --psm 7'
            print("Nenhuma confiança válida obtida com PSM8, tentando PSM7...")
            data = pytesseract.image_to_data(denoised_image, config=custom_config_psm7, output_type=pytesseract.Output.DICT)

        # Se chegou aqui, processa 'data' (seja do PSM8 válido ou do PSM7)
        text = ""
        confidences = []
        for i in range(len(data["text"])):
            char = data["text"][i].strip()
            conf_raw = data["conf"][i]
            try:
                conf = int(conf_raw)
            except Exception:
                try:
                    conf = int(float(conf_raw))
                except Exception:
                    conf = -1

            if char and conf > 0:
                text += char
                confidences.append(conf)

        # Calcula a confiança média
        import numpy as _np
        avg_confidence = _np.mean(confidences) / 100.0 if confidences else 0.0

        # Limpa o texto extraído (remove espaços, caracteres indesejados)
        cleaned_text = "".join(filter(str.isalnum, text)).upper()

        # Logs para depuração
        print(f"OCR raw text: '{text}' -> cleaned: '{cleaned_text}', avg_confidence={avg_confidence:.2f}")

        return cleaned_text, float(avg_confidence)

        text = ""
        confidences = []

        # Filtra caracteres e confianças
        for i in range(len(data["text"])):
            char = data["text"][i].strip()
            conf = int(data["conf"][i])

            if char and conf > 0:  # Ignora caracteres vazios ou com confiança 0
                text += char
                confidences.append(conf)

        # Calcula a confiança média
        avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0

        # Limpa o texto extraído (remove espaços, caracteres indesejados)
        cleaned_text = "".join(filter(str.isalnum, text)).upper()

        return cleaned_text, avg_confidence


if __name__ == "__main__":
    # Exemplo de uso:
    # Certifique-se de ter o Tesseract instalado e configurado.
    # No Ubuntu: sudo apt install tesseract-ocr
    # No Windows: Baixar instalador em https://tesseract-ocr.github.io/tessdoc/Installation.html
    # E adicionar ao PATH ou especificar tesseract_cmd.

    try:
        ocr_engine = OCREngine()

        # Cria uma imagem de teste (simulando uma placa)
        # Em um cenário real, você carregaria uma imagem de um arquivo ou da webcam
        dummy_image = np.zeros((100, 300), dtype=np.uint8) + 255  # Imagem branca
        cv2.putText(dummy_image, "ABC1234", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 5)

        print("\nTestando OCR com imagem dummy:")
        plate_text, confidence = ocr_engine.extract_plate_text(dummy_image)
        print(f"Placa detectada: {plate_text}, Confiança: {confidence:.2f}")

        # Teste com uma imagem mais complexa (simulando ruído)
        noisy_image = np.zeros((100, 300), dtype=np.uint8) + 255
        cv2.putText(noisy_image, "DEF5678", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 5)
        # Adiciona ruído
        noise = np.random.randint(0, 50, noisy_image.shape, dtype=np.uint8)
        noisy_image = cv2.add(noisy_image, noise)

        print("\nTestando OCR com imagem ruidosa:")
        plate_text_noisy, confidence_noisy = ocr_engine.extract_plate_text(noisy_image)
        print(f"Placa detectada: {plate_text_noisy}, Confiança: {confidence_noisy:.2f}")

    except pytesseract.TesseractNotFoundError:
        print("Não foi possível executar o exemplo de OCR. Tesseract não está instalado ou configurado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")