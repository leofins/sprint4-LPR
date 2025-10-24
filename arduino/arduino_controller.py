#!/usr/bin/env python3
"""
Módulo Python para comunicação serial com o Arduino e controle da cancela.
"""

import serial
import time
from typing import Optional

class ArduinoController:
    """Classe para controlar o Arduino via comunicação serial."""
    
    def __init__(self, port: str, baud_rate: int = 9600, timeout: float = 1.0):
        """
        Inicializa o controlador do Arduino.
        
        Args: 
            port: Porta serial onde o Arduino está conectado (ex: 
                  '/dev/ttyACM0' no Linux, 'COM3' no Windows).
            baud_rate: Taxa de transmissão serial (deve ser a mesma configurada no Arduino).
            timeout: Tempo limite para operações de leitura/escrita serial.
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        
        print(f"ArduinoController inicializado para porta {self.port} com baud rate {self.baud_rate}.")

    def connect(self) -> bool:
        """
        Estabelece a conexão serial com o Arduino.
        
        Returns:
            True se a conexão foi estabelecida com sucesso, False caso contrário.
        """
        try:
            self.serial_connection = serial.Serial(
                self.port, 
                self.baud_rate, 
                timeout=self.timeout
            )
            time.sleep(2)  # Espera o Arduino reiniciar após a conexão serial
            print(f"Conexão serial estabelecida com sucesso na porta {self.port}.")
            return True
        except serial.SerialException as e:
            print(f"ERRO: Não foi possível conectar ao Arduino na porta {self.port}: {e}")
            self.serial_connection = None
            return False

    def disconnect(self):
        """
        Fecha a conexão serial com o Arduino.
        """
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print(f"Conexão serial na porta {self.port} fechada.")
        self.serial_connection = None

    def send_command(self, command: str) -> bool:
        """
        Envia um comando para o Arduino.
        
        Args:
            command: O comando a ser enviado (ex: "ABRIR", "FECHAR").
            
        Returns:
            True se o comando foi enviado com sucesso, False caso contrário.
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            print("ERRO: Conexão serial não estabelecida. Tente conectar primeiro.")
            return False
        
        try:
            self.serial_connection.write(f"{command}\n".encode("utf-8"))
            print(f"Comando \"{command}\" enviado para o Arduino.")
            
            # Opcional: Ler a resposta do Arduino para confirmação
            # response = self.serial_connection.readline().decode("utf-8").strip()
            # print(f"Resposta do Arduino: {response}")
            
            return True
        except serial.SerialException as e:
            print(f"ERRO ao enviar comando para o Arduino: {e}")
            self.disconnect()
            return False

    def open_gate(self) -> bool:
        """
        Envia o comando para abrir a cancela.
        """
        return self.send_command("ABRIR")

    def close_gate(self) -> bool:
        """
        Envia o comando para fechar a cancela.
        """
        return self.send_command("FECHAR")

    def __del__(self):
        """
        Garante que a conexão serial seja fechada quando o objeto for destruído.
        """
        self.disconnect()

if __name__ == "__main__":
    # Exemplo de uso:
    # Substitua '/dev/ttyACM0' pela porta serial correta do seu Arduino.
    # No Windows, pode ser algo como 'COM3'.
    
    arduino_port = '/dev/ttyACM0' # Ou 'COM3', '/dev/ttyUSB0', etc.
    
    try:
        controller = ArduinoController(port=arduino_port)
        
        if controller.connect():
            print("\nTestando abertura e fechamento da cancela...")
            
            print("Abrindo cancela em 3 segundos...")
            time.sleep(3)
            controller.open_gate()
            
            print("Fechando cancela em 5 segundos...")
            time.sleep(5)
            controller.close_gate()
            
            print("Abrindo cancela novamente em 3 segundos...")
            time.sleep(3)
            controller.open_gate()
            
            print("Fechando cancela em 5 segundos...")
            time.sleep(5)
            controller.close_gate()
            
            print("Testes concluídos.")
            
        else:
            print("Não foi possível conectar ao Arduino. Verifique a porta e a conexão.")
            
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        if 'controller' in locals():
            controller.disconnect()
