// Código Arduino para controlar um servo motor que simula uma cancela.
// Versão com calibração de pulso para movimento preciso de 90 graus.

#include <Servo.h>

// Define o pino onde o servo motor está conectado
const int servoPin = 9;

// Define os ângulos para a cancela aberta e fechada
const int closedAngle = 0;   // Ângulo para cancela fechada (0 graus)
const int openAngle = 90;    // Ângulo para cancela aberta (90 graus)

// --- MUDANÇA PRINCIPAL AQUI ---
// Calibração de pulso para o servo (em microssegundos)
// O padrão é (544, 2400). A maioria dos servos funciona melhor com (500, 2500).
const int minPulse = 500;
const int maxPulse = 2500;

Servo gateServo; // Cria um objeto servo

void setup() {
  // Anexa o servo ao pino e aplica a calibração de pulso
  gateServo.attach(servoPin, minPulse, maxPulse);
  
  // Inicia a comunicação serial a 9600 bits por segundo
  Serial.begin(9600);
  
  // Garante que a cancela comece fechada
  gateServo.write(closedAngle);
  Serial.println("Cancela inicializada: FECHADA");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    Serial.print("Comando recebido: ");
    Serial.println(command);

    if (command == "ABRIR") {
      gateServo.write(openAngle);
      Serial.println("Cancela: ABERTA");
    } else if (command == "FECHAR") {
      gateServo.write(closedAngle);
      Serial.println("Cancela: FECHADA");
    } else {
      Serial.println("Comando inválido.");
    }
  }
}