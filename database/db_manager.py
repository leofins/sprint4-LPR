#!/usr/bin/env python3
"""
Módulo de gerenciamento do banco de dados SQLite para o sistema de cancela.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List

class DatabaseManager:
    """Classe para gerenciar operações do banco de dados."""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'cancela.db')
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Banco de dados não encontrado: {self.db_path}. Execute init_db.py")
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def verificar_placa_autorizada(self, placa: str) -> Dict[str, any]:
        placa = placa.upper().strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM placas_autorizadas WHERE placa = ?', (placa,))
            resultado = cursor.fetchone()
            if resultado:
                dados = dict(resultado)
                autorizada = dados['status'] == 'AUTORIZADA'
                return {
                    'autorizada': autorizada,
                    'status': dados['status'],
                    'dados': dict(dados)
                }
            else:
                return {'autorizada': False, 'status': 'NAO_ENCONTRADA', 'dados': None}
    
    def registrar_log_acesso(self, placa: str, status_validacao: str, 
                           acao_cancela: str, confianca_ocr: Optional[float] = None,
                           observacoes: Optional[str] = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs_acesso (placa, status_validacao, acao_cancela, confianca_ocr, observacoes)
                VALUES (?, ?, ?, ?, ?)
            ''', (placa.upper().strip(), status_validacao, acao_cancela, confianca_ocr, observacoes))
            conn.commit()
            return cursor.lastrowid
    
    def listar_todas_as_placas(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM placas_autorizadas
                ORDER BY 
                    CASE status
                        WHEN 'AUTORIZADA' THEN 1
                        WHEN 'NAO_AUTORIZADA' THEN 2
                        WHEN 'INATIVA' THEN 3
                        ELSE 4
                    END,
                    data_cadastro DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def adicionar_placa(self, placa: str, status: str, veiculo_modelo: str = None,
                       veiculo_cor: str = None, cliente_nome: str = None) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO placas_autorizadas (placa, status, veiculo_modelo, veiculo_cor, cliente_nome)
                    VALUES (?, ?, ?, ?, ?)
                ''', (placa.upper().strip(), status, veiculo_modelo, veiculo_cor, cliente_nome))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def atualizar_placa(self, placa: str, status: str, veiculo_modelo: str, veiculo_cor: str, cliente_nome: str) -> bool:
        """Atualiza os dados de uma placa existente."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE placas_autorizadas
                    SET status = ?, veiculo_modelo = ?, veiculo_cor = ?, cliente_nome = ?, data_atualizacao = CURRENT_TIMESTAMP
                    WHERE placa = ?
                ''', (status, veiculo_modelo, veiculo_cor, cliente_nome, placa))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar placa: {e}")
            return False

    def desativar_placa(self, placa: str) -> bool:
        """Marca uma placa como INATIVA (soft delete)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE placas_autorizadas
                    SET status = 'INATIVA', data_atualizacao = CURRENT_TIMESTAMP
                    WHERE placa = ?
                ''', (placa,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao desativar placa: {e}")
            return False

    def obter_logs_recentes(self, limite: int = 50) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM logs_acesso ORDER BY timestamp DESC LIMIT ?', (limite,))
            return [dict(row) for row in cursor.fetchall()]
    
    def obter_estatisticas(self) -> Dict[str, any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM placas_autorizadas WHERE status = "AUTORIZADA"')
            total_autorizadas = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM placas_autorizadas WHERE status = "NAO_AUTORIZADA"')
            total_nao_autorizadas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM logs_acesso WHERE DATE(timestamp) = DATE('now', 'localtime')")
            acessos_hoje = cursor.fetchone()[0]
            # --- CORREÇÃO DO ERRO DE DIGITAÇÃO AQUI ---
            cursor.execute("SELECT COUNT(*) FROM logs_acesso WHERE DATE(timestamp) = DATE('now', 'localtime') AND acao_cancela = 'ABERTA'")
            acessos_autorizados_hoje = cursor.fetchone()[0]
            return {
                'total_placas_autorizadas': total_autorizadas,
                'total_placas_nao_autorizadas': total_nao_autorizadas,
                'acessos_hoje': acessos_hoje,
                'taxa_autorizacao_hoje': (acessos_autorizados_hoje / acessos_hoje * 100) if acessos_hoje > 0 else 0
            }