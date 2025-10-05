// Arquivo: cancela_control.ino
// Código Arduino para controlar um servo motor que simula uma cancela.
// Recebe comandos via porta serial para abrir ou fechar a cancela.

#include <Servo.h>

// Define o pino onde o servo motor está conectado
const int servoPin = 9; // Exemplo: pino digital 9

// Define os ângulos para a cancela aberta e fechada
const int closedAngle = 0;   // Ângulo para cancela fechada (0 graus)
const int openAngle = 90;    // Ângulo para cancela aberta (90 graus)

Servo gateServo; // Cria um objeto servo

void setup() {
  // Anexa o servo ao pino especificado
  gateServo.attach(servoPin);
  // Inicia a comunicação serial a 9600 bits por segundo
  Serial.begin(9600);
  
  // Garante que a cancela comece fechada
  gateServo.write(closedAngle);
  Serial.println("Cancela inicializada: FECHADA");
}

void loop() {
  // Verifica se há dados disponíveis na porta serial
  if (Serial.available() > 0) {
    // Lê o comando recebido
    String command = Serial.readStringUntil("\n");
    command.trim(); // Remove espaços em branco (incluindo \r se houver)
    
    Serial.print("Comando recebido: ");
    Serial.println(command);

    // Processa o comando
    if (command == "ABRIR") {
      gateServo.write(openAngle);
      Serial.println("Cancela: ABRINDO");
      delay(1000); // Pequeno atraso para simular movimento
      Serial.println("Cancela: ABERTA");
    } else if (command == "FECHAR") {
      gateServo.write(closedAngle);
      Serial.println("Cancela: FECHANDO");
      delay(1000); // Pequeno atraso para simular movimento
      Serial.println("Cancela: FECHADA");
    } else {
      Serial.println("Comando inválido. Use ABRIR ou FECHAR.");
    }
  }
}

