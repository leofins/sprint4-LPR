# responsável por exibir a imagem: ele vai receber o frame modificado do outro módulo e 
# usará o cv2.imshow para mostrá-lo em sua própria janela, dentro do seu loop principal.

#!/usr/bin/env python3
"""
Aplicação principal do sistema de cancela automatizada.
Integra captura de imagem, OCR, validação de placas e controle do Arduino.
"""

import sys
import os
import time
import threading
import requests
from typing import Optional, Dict, Any
import json
from datetime import datetime
import cv2

# Adiciona os diretórios dos módulos ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr.image_capture import ImageCaptureProcessor
from arduino.arduino_controller import ArduinoController

class CancelaSystem:
    """Classe principal do sistema de cancela automatizada."""
    
    def __init__(self, 
                 api_url: str = "http://localhost:8000",
                 arduino_port: Optional[str] = None,
                 camera_index: int = 0,
                 confidence_threshold: float = 0.7):
        """
        Inicializa o sistema de cancela.
        """
        self.api_url = api_url
        self.arduino_port = arduino_port
        self.camera_index = camera_index
        self.confidence_threshold = confidence_threshold
        self.image_processor: Optional[ImageCaptureProcessor] = None
        self.arduino_controller: Optional[ArduinoController] = None
        self.running = False
        self.last_processed_plate = None
        self.last_processed_time = None
        self.plate_cooldown = 5.0  # Cooldown para não processar a mesma placa repetidamente
        self.gate_open_duration = 3.0 # Segundos que a cancela fica aberta
        
        # Lock para evitar condição de corrida ao acessar dados compartilhados entre threads
        self.processing_lock = threading.Lock()
        
        print(f"Sistema de Cancela inicializado:")
        print(f"  - API URL: {self.api_url}")
        print(f"  - Arduino Port: {self.arduino_port or 'Nenhum'}")
        print(f"  - Camera Index: {self.camera_index}")
        print(f"  - Confidence Threshold: {self.confidence_threshold}")

    def initialize_components(self) -> bool:
        """
        Inicializa todos os componentes do sistema.
        """
        print("\nInicializando componentes do sistema...")
        try:
            self.image_processor = ImageCaptureProcessor(camera_index=self.camera_index)
            print("✅ Processador de imagem inicializado.")
        except Exception as e:
            print(f"❌ Erro ao inicializar processador de imagem: {e}")
            return False
        
        if self.arduino_port:
            try:
                self.arduino_controller = ArduinoController(port=self.arduino_port)
                if self.arduino_controller.connect():
                    print("✅ Controlador Arduino inicializado.")
                else:
                    self.arduino_controller = None
            except Exception as e:
                self.arduino_controller = None
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API de validação conectada.")
        except Exception as e:
            print(f"❌ Erro ao conectar com a API: {e}")
            return False
        
        return True

    def validate_plate_with_api(self, plate: str, confidence: float) -> Dict[str, Any]:
        """
        Valida uma placa usando a API.
        """
        try:
            payload = {"placa": plate, "confianca_ocr": confidence}
            response = requests.post(f"{self.api_url}/validar-placa", json=payload, timeout=10)
            return response.json()
        except Exception as e:
            return {"autorizada": False, "status": "ERRO_CONEXAO", "acao_cancela": "FECHADA"}

    def control_gate(self, action: str) -> bool:
        """
        Controla a cancela física via Arduino.
        """
        if not self.arduino_controller:
            print(f"(Simulando Ação: Cancela {action})")
            return True
        
        try:
            if action == "ABRIR":
                return self.arduino_controller.open_gate()
            elif action == "FECHAR":
                print("🚪 Comando para fechar a cancela enviado.")
                return self.arduino_controller.close_gate()
            return False
        except Exception as e:
            print(f"Erro ao controlar cancela: {e}")
            return False

    def process_detected_plate(self, plate_info: Dict[str, Any]):
        """
        Processa uma placa detectada (executado em uma thread separada).
        """
        plate = plate_info["placa"]
        confidence = plate_info["confianca"]
        
        # Usamos um lock para garantir que a checagem e a atualização do estado
        # não aconteçam ao mesmo tempo por múltiplas threads.
        with self.processing_lock:
            current_time = time.time()
            if (self.last_processed_plate == plate and 
                current_time - self.last_processed_time < self.plate_cooldown):
                return  # Ignora a placa pois foi processada recentemente

            # Atualiza o tempo imediatamente para que outras threads já saibam
            self.last_processed_plate = plate
            self.last_processed_time = time.time()

        print(f"\n🔍 Placa detectada: {plate} (Confiança: {confidence:.2f})")
        
        if confidence < self.confidence_threshold:
            print(f"⚠️  Confiança baixa. Ignorando.")
            return

        validation_result = self.validate_plate_with_api(plate, confidence)
        autorizada = validation_result.get("autorizada", False)
        
        # --- LÓGICA DE AUTO-CLOSE AQUI ---
        if autorizada:
            print(f"✅ Placa {plate} AUTORIZADA - Abrindo cancela.")
            if self.control_gate("ABRIR"):
                print(f"🚪 Cancela ABERTA. Fechará em {self.gate_open_duration} segundos.")
                # Agenda o fechamento da cancela para daqui a X segundos
                timer = threading.Timer(self.gate_open_duration, self.control_gate, args=["FECHAR"])
                timer.start()
        else:
            status = validation_result.get("status", "DESCONHECIDO")
            print(f"❌ Placa {plate} NÃO AUTORIZADA ({status})")
            self.control_gate("FECHAR") # Garante que a cancela permaneça fechada

    def run_detection_loop(self):
        """
        Loop principal de detecção de placas. Otimizado para não travar a UI.
        """
        print("\n🚀 Iniciando loop de detecção de placas...")
        print("Pressione 'q' na janela da webcam para parar o sistema.")
        
        while self.running:
            try:
                frame, plate_info = self.image_processor.capture_and_process_frame()
                
                if frame is not None:
                    cv2.imshow("Sistema de Cancela - TCC", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop()
                    break

                # --- OTIMIZAÇÃO DE PERFORMANCE AQUI ---
                if plate_info:
                    # Dispara o processamento pesado em uma nova thread para
                    # não bloquear a exibição do vídeo.
                    thread = threading.Thread(target=self.process_detected_plate, args=(plate_info,))
                    thread.start()
                
            except Exception as e:
                print(f"❌ Erro no loop de detecção: {e}")
                time.sleep(1)

    def start(self):
        if not self.initialize_components():
            return
        self.running = True
        self.run_detection_loop()

    def stop(self):
        if not self.running: return
        print("\n🛑 Parando Sistema de Cancela...")
        self.running = False
        time.sleep(0.5) # Dá um tempo para as threads finalizarem
        if self.arduino_controller:
            self.control_gate("FECHAR")
            self.arduino_controller.disconnect()
        cv2.destroyAllWindows()
        print("✅ Sistema parado com sucesso!")

    def run_interactive_mode(self):
        try:
            self.start()
        finally:
            self.stop()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sistema de Cancela Automatizada")
    parser.add_argument("--api-url", default="http://localhost:8000", help="URL da API")
    parser.add_argument("--arduino-port", default=None, help="Porta serial do Arduino")
    parser.add_argument("--camera", type=int, default=0, help="Índice da câmera")
    parser.add_argument("--confidence", type=float, default=0.7, help="Confiança mínima do OCR")
    args = parser.parse_args()
    system = CancelaSystem(api_url=args.api_url, arduino_port=args.arduino_port, camera_index=args.camera, confidence_threshold=args.confidence)
    system.run_interactive_mode()

if __name__ == "__main__":
    main()