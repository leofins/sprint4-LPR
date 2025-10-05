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

# Adiciona os diretórios dos módulos ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr.image_capture import ImageCaptureProcessor
from arduino.arduino_controller import ArduinoController

class CancelaSystem:
    """Classe principal do sistema de cancela automatizada."""
    
    def __init__(self, 
                 api_url: str = "http://localhost:8000",
                 arduino_port: str = "/dev/ttyACM0",
                 camera_index: int = 0,
                 confidence_threshold: float = 0.7):
        """
        Inicializa o sistema de cancela.
        
        Args:
            api_url: URL da API de validação de placas.
            arduino_port: Porta serial do Arduino.
            camera_index: Índice da câmera.
            confidence_threshold: Limite mínimo de confiança do OCR.
        """
        self.api_url = api_url
        self.arduino_port = arduino_port
        self.camera_index = camera_index
        self.confidence_threshold = confidence_threshold
        
        # Componentes do sistema
        self.image_processor: Optional[ImageCaptureProcessor] = None
        self.arduino_controller: Optional[ArduinoController] = None
        
        # Estado do sistema
        self.running = False
        self.last_processed_plate = None
        self.last_processed_time = None
        self.plate_cooldown = 5.0  # Segundos para evitar processamento repetido
        
        print(f"Sistema de Cancela inicializado:")
        print(f"  - API URL: {self.api_url}")
        print(f"  - Arduino Port: {self.arduino_port}")
        print(f"  - Camera Index: {self.camera_index}")
        print(f"  - Confidence Threshold: {self.confidence_threshold}")

    def initialize_components(self) -> bool:
        """
        Inicializa todos os componentes do sistema.
        
        Returns:
            True se todos os componentes foram inicializados com sucesso.
        """
        print("\nInicializando componentes do sistema...")
        
        # Inicializa o processador de imagem
        try:
            self.image_processor = ImageCaptureProcessor(camera_index=self.camera_index)
            print("✅ Processador de imagem inicializado.")
        except Exception as e:
            print(f"❌ Erro ao inicializar processador de imagem: {e}")
            return False
        
        # Inicializa o controlador do Arduino
        try:
            self.arduino_controller = ArduinoController(port=self.arduino_port)
            if self.arduino_controller.connect():
                print("✅ Controlador Arduino inicializado.")
            else:
                print("⚠️  Arduino não conectado. Sistema funcionará sem controle físico.")
        except Exception as e:
            print(f"⚠️  Erro ao inicializar Arduino: {e}")
            print("Sistema funcionará sem controle físico.")
        
        # Testa a conexão com a API
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API de validação conectada.")
            else:
                print(f"⚠️  API respondeu com status {response.status_code}")
        except Exception as e:
            print(f"❌ Erro ao conectar com a API: {e}")
            return False
        
        return True

    def validate_plate_with_api(self, plate: str, confidence: float) -> Dict[str, Any]:
        """
        Valida uma placa usando a API.
        
        Args:
            plate: Placa detectada.
            confidence: Confiança do OCR.
            
        Returns:
            Resposta da API com o status de validação.
        """
        try:
            payload = {
                "placa": plate,
                "confianca_ocr": confidence
            }
            
            response = requests.post(
                f"{self.api_url}/validar-placa",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro na API: {response.status_code} - {response.text}")
                return {"autorizada": False, "status": "ERRO_API", "acao_cancela": "FECHADA"}
                
        except Exception as e:
            print(f"Erro ao validar placa com API: {e}")
            return {"autorizada": False, "status": "ERRO_CONEXAO", "acao_cancela": "FECHADA"}

    def control_gate(self, action: str) -> bool:
        """
        Controla a cancela física via Arduino.
        
        Args:
            action: Ação a ser executada ("ABERTA" ou "FECHADA").
            
        Returns:
            True se o comando foi enviado com sucesso.
        """
        if not self.arduino_controller:
            print("Arduino não conectado. Simulando ação da cancela.")
            return True
        
        try:
            if action == "ABERTA":
                return self.arduino_controller.open_gate()
            elif action == "FECHADA":
                return self.arduino_controller.close_gate()
            else:
                print(f"Ação inválida: {action}")
                return False
        except Exception as e:
            print(f"Erro ao controlar cancela: {e}")
            return False

    def should_process_plate(self, plate: str) -> bool:
        """
        Verifica se uma placa deve ser processada (evita processamento repetido).
        
        Args:
            plate: Placa detectada.
            
        Returns:
            True se a placa deve ser processada.
        """
        current_time = time.time()
        
        if (self.last_processed_plate == plate and 
            self.last_processed_time and 
            current_time - self.last_processed_time < self.plate_cooldown):
            return False
        
        return True

    def process_detected_plate(self, plate_info: Dict[str, Any]):
        """
        Processa uma placa detectada.
        
        Args:
            plate_info: Informações da placa detectada.
        """
        plate = plate_info["placa"]
        confidence = plate_info["confianca"]
        
        print(f"\n🔍 Placa detectada: {plate} (Confiança: {confidence:.2f})")
        
        # Verifica se a confiança é suficiente
        if confidence < self.confidence_threshold:
            print(f"⚠️  Confiança baixa ({confidence:.2f} < {self.confidence_threshold}). Ignorando.")
            return
        
        # Verifica se deve processar esta placa
        if not self.should_process_plate(plate):
            print(f"⏭️  Placa {plate} processada recentemente. Ignorando.")
            return
        
        # Valida a placa com a API
        print(f"🔄 Validando placa {plate} com a API...")
        validation_result = self.validate_plate_with_api(plate, confidence)
        
        # Processa o resultado
        autorizada = validation_result.get("autorizada", False)
        status = validation_result.get("status", "DESCONHECIDO")
        acao_cancela = validation_result.get("acao_cancela", "FECHADA")
        
        if autorizada:
            print(f"✅ Placa {plate} AUTORIZADA - Abrindo cancela")
        else:
            print(f"❌ Placa {plate} NÃO AUTORIZADA ({status}) - Cancela permanece fechada")
        
        # Controla a cancela física
        gate_success = self.control_gate(acao_cancela)
        if gate_success:
            print(f"🚪 Cancela: {acao_cancela}")
        else:
            print(f"⚠️  Erro ao controlar cancela")
        
        # Atualiza o estado
        self.last_processed_plate = plate
        self.last_processed_time = time.time()
        
        # Log detalhado
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"📝 Log: [{timestamp}] {plate} | {status} | {acao_cancela} | Conf: {confidence:.2f}")

    def run_detection_loop(self):
        """
        Loop principal de detecção de placas.
        """
        print("\n🚀 Iniciando loop de detecção de placas...")
        print("Pressione Ctrl+C para parar o sistema.")
        
        while self.running:
            try:
                # Captura e processa frame
                plate_info = self.image_processor.capture_and_process_frame()
                
                if plate_info:
                    self.process_detected_plate(plate_info)
                
                # Pequeno delay para evitar sobrecarga da CPU
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n🛑 Interrupção detectada. Parando sistema...")
                self.stop()
                break
            except Exception as e:
                print(f"❌ Erro no loop de detecção: {e}")
                time.sleep(1)  # Pausa antes de tentar novamente

    def start(self):
        """
        Inicia o sistema de cancela.
        """
        print("\n🔄 Iniciando Sistema de Cancela...")
        
        if not self.initialize_components():
            print("❌ Falha na inicialização dos componentes. Sistema não pode ser iniciado.")
            return False
        
        self.running = True
        
        # Inicia o loop de detecção em uma thread separada
        detection_thread = threading.Thread(target=self.run_detection_loop)
        detection_thread.daemon = True
        detection_thread.start()
        
        print("✅ Sistema iniciado com sucesso!")
        return True

    def stop(self):
        """
        Para o sistema de cancela.
        """
        print("\n🛑 Parando Sistema de Cancela...")
        self.running = False
        
        # Fecha a cancela antes de parar
        if self.arduino_controller:
            print("🚪 Fechando cancela...")
            self.control_gate("FECHADA")
            self.arduino_controller.disconnect()
        
        print("✅ Sistema parado com sucesso!")

    def run_interactive_mode(self):
        """
        Executa o sistema em modo interativo.
        """
        if not self.start():
            return
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sistema de Cancela Automatizada")
    parser.add_argument("--api-url", default="http://localhost:8000", 
                       help="URL da API de validação")
    parser.add_argument("--arduino-port", default="/dev/ttyACM0", 
                       help="Porta serial do Arduino")
    parser.add_argument("--camera", type=int, default=0, 
                       help="Índice da câmera")
    parser.add_argument("--confidence", type=float, default=0.7, 
                       help="Limite mínimo de confiança do OCR")
    parser.add_argument("--test-mode", action="store_true", 
                       help="Executa em modo de teste (sem Arduino)")
    
    args = parser.parse_args()
    
    # Ajusta a porta do Arduino para modo de teste
    arduino_port = None if args.test_mode else args.arduino_port
    
    # Cria e executa o sistema
    system = CancelaSystem(
        api_url=args.api_url,
        arduino_port=arduino_port,
        camera_index=args.camera,
        confidence_threshold=args.confidence
    )
    
    system.run_interactive_mode()

if __name__ == "__main__":
    main()
