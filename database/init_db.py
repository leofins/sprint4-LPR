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
    
    db_path = os.path.join(os.path.dirname(__file__), 'cancela.db')
    
    # --- IMPORTANTE: REMOVE O BANCO ANTIGO SE EXISTIR ---
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Banco de dados antigo removido em: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # --- CORREÇÃO 1 AQUI ---
    # Adiciona 'INATIVA' à lista de status permitidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placas_autorizadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('AUTORIZADA', 'NAO_AUTORIZADA', 'INATIVA')),
            veiculo_modelo TEXT,
            veiculo_cor TEXT,
            cliente_nome TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_placa ON placas_autorizadas(placa)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs_acesso(timestamp)')
    
    conn.commit()
    print(f"Novo banco de dados criado com sucesso em: {db_path}")
    
    return conn, cursor

def insert_sample_data(cursor):
    """Insere dados de exemplo no banco de dados."""
    
    # --- CORREÇÃO 2 AQUI ---
    # Corrigindo 'AUTORIZADO' para 'AUTORIZADA' e 'NAO_AUTORIZADO' para 'NAO_AUTORIZADA'
    placas_exemplo = [
        ('OTM2X22', 'AUTORIZADA', 'Volkswagen Gol', 'Azul', 'Leonardo Henrique'),
        ('OTM2022', 'NAO_AUTORIZADA', 'Volkswagen Gol', 'Azul', 'Tiago Rosto'),
        ('HQW5678', 'AUTORIZADA', 'Tesla', 'Azul', 'Gabriel Reno'),
        ('DOK2A20', 'NAO_AUTORIZADA', 'Volkswagen Gol', 'Preto', 'Luis Felipe'),
        ('ABC1234', 'AUTORIZADA', 'Honda Civic', 'Prata', 'João Silva'),
        ('ABC1B34', 'AUTORIZADA', 'Tesla', 'Prata', 'Paulo Vinicius'),
        ('ABC1C34', 'AUTORIZADA', 'Toyota SW4', 'Prata', 'Maria Alzira'),
        ('ABC1D34', 'AUTORIZADA', 'Toyota SW4', '', 'Daniel Rodrigo'),
        ('XYZ5678', 'NAO_AUTORIZADA', 'Volkswagen Gol', 'Azul', 'Pedro Oliveira'),
        ('DEF9G12', 'AUTORIZADA', 'Volkswagen Gol', 'Azul', 'Pedro Oliveira'),
        ('QRT4E56', 'AUTORIZADA', 'Toyota SW4', '', 'Virgilio Santos'),
        ('DEF5678', 'AUTORIZADA', 'Toyota Corolla', 'Branco', 'Maria Santos'),
        ('GHI9012', 'AUTORIZADA', 'Volkswagen Gol', 'Azul', 'Pedro Oliveira'),
        ('JKL3456', 'NAO_AUTORIZADA', 'Ford Ka', 'Vermelho', 'Pedro Nunes'),
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
    print("Inicializando banco de dados do sistema de cancela...")
    conn, cursor = create_database()
    insert_sample_data(cursor)
    conn.commit()
    conn.close()
    print("Inicialização do banco de dados concluída com sucesso!")

if __name__ == "__main__":
    main()