#!/usr/bin/env python3
"""
Módulo de gerenciamento do banco de dados SQLite para o sistema de cancela.
Fornece funções para consultar placas autorizadas e registrar logs de acesso.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple

class DatabaseManager:
    """Classe para gerenciar operações do banco de dados."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa o gerenciador do banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados.
                    Se None, usa o caminho padrão.
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'cancela.db')
        
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Garante que o banco de dados existe."""
        if not os.path.exists(self.db_path):
            print(f"Banco de dados não encontrado em {self.db_path}")
            print("Execute o script init_db.py para criar o banco de dados.")
            raise FileNotFoundError(f"Banco de dados não encontrado: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Retorna uma conexão com o banco de dados."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome da coluna
        return conn
    
    def verificar_placa_autorizada(self, placa: str) -> Dict[str, any]:
        """
        Verifica se uma placa está autorizada no banco de dados.
        
        Args:
            placa: Placa do veículo a ser verificada.
            
        Returns:
            Dicionário com informações da placa:
            - autorizada: bool
            - status: str
            - dados: dict com informações do veículo (se encontrado)
        """
        placa = placa.upper().strip()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM placas_autorizadas 
                WHERE placa = ?
            ''', (placa,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                dados = dict(resultado)
                autorizada = dados['status'] == 'AUTORIZADA'
                
                return {
                    'autorizada': autorizada,
                    'status': dados['status'],
                    'dados': {
                        'placa': dados['placa'],
                        'veiculo_modelo': dados['veiculo_modelo'],
                        'veiculo_cor': dados['veiculo_cor'],
                        'cliente_nome': dados['cliente_nome'],
                        'data_cadastro': dados['data_cadastro']
                    }
                }
            else:
                return {
                    'autorizada': False,
                    'status': 'NAO_ENCONTRADA',
                    'dados': None
                }
    
    def registrar_log_acesso(self, placa: str, status_validacao: str, 
                           acao_cancela: str, confianca_ocr: Optional[float] = None,
                           observacoes: Optional[str] = None) -> int:
        """
        Registra um log de acesso no banco de dados.
        
        Args:
            placa: Placa do veículo.
            status_validacao: Status da validação (AUTORIZADA, NAO_AUTORIZADA, NAO_ENCONTRADA).
            acao_cancela: Ação realizada na cancela (ABERTA, FECHADA).
            confianca_ocr: Nível de confiança do OCR (0.0 a 1.0).
            observacoes: Observações adicionais.
            
        Returns:
            ID do log inserido.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO logs_acesso 
                (placa, status_validacao, acao_cancela, confianca_ocr, observacoes)
                VALUES (?, ?, ?, ?, ?)
            ''', (placa.upper().strip(), status_validacao, acao_cancela, 
                  confianca_ocr, observacoes))
            
            conn.commit()
            return cursor.lastrowid
    
    def listar_placas_autorizadas(self) -> List[Dict]:
        """
        Lista todas as placas autorizadas.
        
        Returns:
            Lista de dicionários com dados das placas autorizadas.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM placas_autorizadas 
                WHERE status = 'AUTORIZADA'
                ORDER BY placa
            ''')
            
            resultados = cursor.fetchall()
            return [dict(row) for row in resultados]
    
    def adicionar_placa(self, placa: str, status: str, veiculo_modelo: str = None,
                       veiculo_cor: str = None, cliente_nome: str = None) -> bool:
        """
        Adiciona uma nova placa ao banco de dados.
        
        Args:
            placa: Placa do veículo.
            status: Status da placa (AUTORIZADA ou NAO_AUTORIZADA).
            veiculo_modelo: Modelo do veículo.
            veiculo_cor: Cor do veículo.
            cliente_nome: Nome do cliente.
            
        Returns:
            True se a placa foi adicionada com sucesso, False caso contrário.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO placas_autorizadas 
                    (placa, status, veiculo_modelo, veiculo_cor, cliente_nome)
                    VALUES (?, ?, ?, ?, ?)
                ''', (placa.upper().strip(), status, veiculo_modelo, 
                      veiculo_cor, cliente_nome))
                
                conn.commit()
                return True
                
        except sqlite3.IntegrityError:
            return False  # Placa já existe
    
    def atualizar_status_placa(self, placa: str, novo_status: str) -> bool:
        """
        Atualiza o status de uma placa existente.
        
        Args:
            placa: Placa do veículo.
            novo_status: Novo status (AUTORIZADA ou NAO_AUTORIZADA).
            
        Returns:
            True se a placa foi atualizada com sucesso, False caso contrário.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE placas_autorizadas 
                SET status = ?, data_atualizacao = CURRENT_TIMESTAMP
                WHERE placa = ?
            ''', (novo_status, placa.upper().strip()))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def obter_logs_recentes(self, limite: int = 50) -> List[Dict]:
        """
        Obtém os logs de acesso mais recentes.
        
        Args:
            limite: Número máximo de logs a retornar.
            
        Returns:
            Lista de dicionários com os logs de acesso.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM logs_acesso 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limite,))
            
            resultados = cursor.fetchall()
            return [dict(row) for row in resultados]
    
    def obter_estatisticas(self) -> Dict[str, any]:
        """
        Obtém estatísticas do sistema.
        
        Returns:
            Dicionário com estatísticas do sistema.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total de placas autorizadas
            cursor.execute('SELECT COUNT(*) FROM placas_autorizadas WHERE status = "AUTORIZADA"')
            total_autorizadas = cursor.fetchone()[0]
            
            # Total de placas não autorizadas
            cursor.execute('SELECT COUNT(*) FROM placas_autorizadas WHERE status = "NAO_AUTORIZADA"')
            total_nao_autorizadas = cursor.fetchone()[0]
            
            # Total de acessos hoje
            cursor.execute('''
                SELECT COUNT(*) FROM logs_acesso 
                WHERE DATE(timestamp) = DATE('now')
            ''')
            acessos_hoje = cursor.fetchone()[0]
            
            # Acessos autorizados hoje
            cursor.execute('''
                SELECT COUNT(*) FROM logs_acesso 
                WHERE DATE(timestamp) = DATE('now') 
                AND acao_cancela = 'ABERTA'
            ''')
            acessos_autorizados_hoje = cursor.fetchone()[0]
            
            return {
                'total_placas_autorizadas': total_autorizadas,
                'total_placas_nao_autorizadas': total_nao_autorizadas,
                'acessos_hoje': acessos_hoje,
                'acessos_autorizados_hoje': acessos_autorizados_hoje,
                'taxa_autorizacao_hoje': (acessos_autorizados_hoje / acessos_hoje * 100) if acessos_hoje > 0 else 0
            }
