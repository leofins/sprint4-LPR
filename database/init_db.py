#!/usr/bin/env python3
"""
Script de inicialização do banco de dados SQLite para o sistema de cancela.
Cria as tabelas necessárias e insere dados de exemplo.
"""

import sqlite3
import os
from datetime import datetime

def create_database():
    """Cria o banco de dados e as tabelas necessárias."""
    
    # Caminho do banco de dados
    db_path = os.path.join(os.path.dirname(__file__), 'cancela.db')
    
    # Conecta ao banco de dados (cria se não existir)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cria a tabela de placas autorizadas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placas_autorizadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('AUTORIZADA', 'NAO_AUTORIZADA')),
            veiculo_modelo TEXT,
            veiculo_cor TEXT,
            cliente_nome TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Cria a tabela de logs de acesso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_acesso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            status_validacao TEXT NOT NULL,
            acao_cancela TEXT NOT NULL CHECK (acao_cancela IN ('ABERTA', 'FECHADA')),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confianca_ocr REAL,
            observacoes TEXT
        )
    ''')
    
    # Cria índices para melhor performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_placa ON placas_autorizadas(placa)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs_acesso(timestamp)')
    
    conn.commit()
    print(f"Banco de dados criado com sucesso em: {db_path}")
    
    return conn, cursor

def insert_sample_data(cursor):
    """Insere dados de exemplo no banco de dados."""
    
    placas_exemplo = [
        ('ABC1234', 'AUTORIZADA', 'Honda Civic', 'Prata', 'João Silva'),
        ('DEF5678', 'AUTORIZADA', 'Toyota Corolla', 'Branco', 'Maria Santos'),
        ('GHI9012', 'AUTORIZADA', 'Volkswagen Gol', 'Azul', 'Pedro Oliveira'),
        ('JKL3456', 'NAO_AUTORIZADA', 'Ford Ka', 'Vermelho', 'Ana Costa'),
        ('MNO7890', 'AUTORIZADA', 'Chevrolet Onix', 'Preto', 'Carlos Ferreira'),
        ('PQR1357', 'AUTORIZADA', 'Hyundai HB20', 'Branco', 'Lucia Almeida'),
        ('STU2468', 'NAO_AUTORIZADA', 'Fiat Uno', 'Prata', 'Roberto Lima'),
        ('VWX9753', 'AUTORIZADA', 'Nissan March', 'Azul', 'Fernanda Rocha'),
        ('YZA1470', 'AUTORIZADA', 'Renault Sandero', 'Vermelho', 'Marcos Souza'),
        ('BCD8520', 'NAO_AUTORIZADA', 'Peugeot 208', 'Preto', 'Juliana Martins')
    ]
    
    for placa, status, modelo, cor, cliente in placas_exemplo:
        try:
            cursor.execute('''
                INSERT INTO placas_autorizadas 
                (placa, status, veiculo_modelo, veiculo_cor, cliente_nome)
                VALUES (?, ?, ?, ?, ?)
            ''', (placa, status, modelo, cor, cliente))
        except sqlite3.IntegrityError:
            print(f"Placa {placa} já existe no banco de dados.")
    
    print(f"Inseridos {len(placas_exemplo)} registros de exemplo.")

def main():
    """Função principal para inicializar o banco de dados."""
    
    print("Inicializando banco de dados do sistema de cancela...")
    
    # Cria o banco de dados e tabelas
    conn, cursor = create_database()
    
    # Insere dados de exemplo
    insert_sample_data(cursor)
    
    # Confirma as alterações e fecha a conexão
    conn.commit()
    conn.close()
    
    print("Inicialização do banco de dados concluída com sucesso!")

if __name__ == "__main__":
    main()
