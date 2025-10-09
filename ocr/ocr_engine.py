'''
Este módulo contém a classe OCREngine, responsável por processar imagens 
e extrair texto de placas de veículos usando a biblioteca EasyOCR.
'''

import re
import easyocr
import numpy as np

# Padrões de placas (Mercosul e modelos anteriores)
PLATE_PATTERNS = [
    re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$"),  # Mercosul (ABC1D23)
    re.compile(r"^[A-Z]{3}[0-9]{4}$"),              # Padrão antigo (ABC1234)
]

class OCREngine:
    '''Motor de OCR para reconhecimento de placas de veículos usando EasyOCR.'''

    def __init__(self, languages=['pt']):
        '''
        Inicializa o leitor EasyOCR.

        Args:
            languages (list): Lista de idiomas para o EasyOCR. Padrão é ['pt'].
        '''
        try:
            print("Inicializando o motor EasyOCR (isso pode levar um tempo na primeira execução)...")
            self.reader = easyocr.Reader(languages, gpu=False)  # gpu=False para compatibilidade
            print("✅ Motor EasyOCR inicializado com sucesso.")
        except Exception as e:
            print(f"❌ ERRO: Falha ao inicializar o EasyOCR. {e}")
            print("Por favor, certifique-se de que as dependências (PyTorch, EasyOCR) estão instaladas corretamente.")
            raise

    def normalize_by_position(self, text: str) -> str:
        '''
        Normaliza o texto da placa com base na posição dos caracteres,
        corrigindo erros comuns de OCR (ex: I -> 1, O -> 0).
        '''
        mapping = { "I": "1", "O": "0", "S": "5", "G": "6", "Z": "2", "B": "8" }
        
        # Padrão Mercosul (LLLNLNN)
        if len(text) == 7 and text[0:3].isalpha() and text[4].isalpha() and text[3].isdigit() and text[5:7].isdigit():
            return "".join(
                mapping.get(char, char) if i in [3, 5, 6] else char
                for i, char in enumerate(text)
            )
        # Padrão antigo (LLLNNNN)
        elif len(text) == 7 and text[0:3].isalpha() and text[3:7].isdigit():
            return "".join(
                mapping.get(char, char) if i >= 3 else char
                for i, char in enumerate(text)
            )
        return text

    def extract_plate_info(self, image: np.ndarray):
        '''
        Extrai o texto da placa de uma imagem, filtra e normaliza.

        Args:
            image (np.ndarray): Imagem (frame da câmera) para processar.

        Returns:
            dict: Um dicionário com a placa, confiança e bounding box, ou None se nenhuma placa válida for encontrada.
        '''
        try:
            results = self.reader.readtext(image)
        except Exception as e:
            print(f"❌ ERRO ao executar o readtext do EasyOCR: {e}")
            return None

        best_match = None
        max_confidence = 0.0

        for (bbox, text, prob) in results:
            cleaned_text = "".join(filter(str.isalnum, text)).upper()
            normalized_text = self.normalize_by_position(cleaned_text)

            for pattern in PLATE_PATTERNS:
                if pattern.match(normalized_text):
                    if prob > max_confidence:
                        max_confidence = prob
                        best_match = {
                            "placa": normalized_text,
                            "confianca": prob,
                            "bbox": bbox
                        }
                        
        return best_match



