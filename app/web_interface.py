#!/usr/bin/env python3
"""
Interface web simples para monitoramento do sistema de cancela.
Utiliza Flask para criar uma interface de monitoramento em tempo real.
"""

from flask import Flask, render_template, jsonify, request
import sys
import os
import requests
from datetime import datetime
import json

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sistema_cancela_2024'

# Configurações
API_URL = "http://localhost:8000"
db_manager = DatabaseManager()

@app.route('/')
def index():
    """Página principal do dashboard."""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Endpoint para obter estatísticas do sistema."""
    try:
        stats = db_manager.obter_estatisticas()
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/logs')
def get_logs():
    """Endpoint para obter logs recentes."""
    try:
        limite = request.args.get('limite', 20, type=int)
        logs = db_manager.obter_logs_recentes(limite)
        return jsonify({
            'success': True,
            'data': logs,
            'total': len(logs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/placas')
def get_placas():
    """Endpoint para obter placas autorizadas."""
    try:
        placas = db_manager.listar_placas_autorizadas()
        return jsonify({
            'success': True,
            'data': placas,
            'total': len(placas)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate', methods=['POST'])
def validate_plate():
    """Endpoint para validar uma placa manualmente."""
    try:
        data = request.get_json()
        placa = data.get('placa', '').strip().upper()
        
        if not placa:
            return jsonify({
                'success': False,
                'error': 'Placa não fornecida'
            }), 400
        
        # Faz a validação via API principal
        response = requests.post(f"{API_URL}/validar-placa", json={
            'placa': placa,
            'confianca_ocr': 1.0  # Validação manual tem confiança máxima
        }, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Erro na API: {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/add-plate', methods=['POST'])
def add_plate():
    """Endpoint para adicionar uma nova placa."""
    try:
        data = request.get_json()
        placa = data.get('placa', '').strip().upper()
        status = data.get('status', 'AUTORIZADA')
        modelo = data.get('modelo', '')
        cor = data.get('cor', '')
        cliente = data.get('cliente', '')
        
        if not placa:
            return jsonify({
                'success': False,
                'error': 'Placa não fornecida'
            }), 400
        
        sucesso = db_manager.adicionar_placa(
            placa=placa,
            status=status,
            veiculo_modelo=modelo,
            veiculo_cor=cor,
            cliente_nome=cliente
        )
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Placa adicionada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Placa já existe no sistema'
            }), 409
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Cria o template HTML
template_html = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Cancela - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            opacity: 0.9;
        }
        
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-card h3 {
            color: #667eea;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .stat-card p {
            color: #666;
            font-size: 0.9rem;
        }
        
        .section {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            overflow: hidden;
        }
        
        .section-header {
            background: #f8f9fa;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #e9ecef;
        }
        
        .section-header h2 {
            color: #495057;
            font-size: 1.2rem;
        }
        
        .section-content {
            padding: 1.5rem;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
        }
        
        .btn {
            background: #667eea;
            color: white;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #5a6fd8;
        }
        
        .btn-success {
            background: #28a745;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .table th, .table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        
        .table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        
        .badge {
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Sistema de Cancela</h1>
        <p>Dashboard de Monitoramento e Controle</p>
    </div>
    
    <div class="container">
        <!-- Estatísticas -->
        <div class="stats-grid" id="stats-grid">
            <div class="stat-card">
                <h3 id="stat-autorizadas">-</h3>
                <p>Placas Autorizadas</p>
            </div>
            <div class="stat-card">
                <h3 id="stat-nao-autorizadas">-</h3>
                <p>Placas Não Autorizadas</p>
            </div>
            <div class="stat-card">
                <h3 id="stat-acessos-hoje">-</h3>
                <p>Acessos Hoje</p>
            </div>
            <div class="stat-card">
                <h3 id="stat-taxa-autorizacao">-</h3>
                <p>Taxa de Autorização</p>
            </div>
        </div>
        
        <!-- Validação Manual -->
        <div class="section">
            <div class="section-header">
                <h2>Validação Manual de Placa</h2>
            </div>
            <div class="section-content">
                <div id="validation-message"></div>
                <form id="validation-form">
                    <div class="form-group">
                        <label for="placa-input">Placa do Veículo:</label>
                        <input type="text" id="placa-input" placeholder="Ex: ABC1234" maxlength="8" style="text-transform: uppercase;">
                    </div>
                    <button type="submit" class="btn">Validar Placa</button>
                </form>
            </div>
        </div>
        
        <!-- Adicionar Nova Placa -->
        <div class="section">
            <div class="section-header">
                <h2>Adicionar Nova Placa</h2>
            </div>
            <div class="section-content">
                <div id="add-plate-message"></div>
                <form id="add-plate-form">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                        <div class="form-group">
                            <label for="nova-placa">Placa:</label>
                            <input type="text" id="nova-placa" placeholder="ABC1234" maxlength="8" required style="text-transform: uppercase;">
                        </div>
                        <div class="form-group">
                            <label for="status-placa">Status:</label>
                            <select id="status-placa" required>
                                <option value="AUTORIZADA">Autorizada</option>
                                <option value="NAO_AUTORIZADA">Não Autorizada</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="modelo-veiculo">Modelo:</label>
                            <input type="text" id="modelo-veiculo" placeholder="Honda Civic">
                        </div>
                        <div class="form-group">
                            <label for="cor-veiculo">Cor:</label>
                            <input type="text" id="cor-veiculo" placeholder="Prata">
                        </div>
                        <div class="form-group">
                            <label for="nome-cliente">Cliente:</label>
                            <input type="text" id="nome-cliente" placeholder="João Silva">
                        </div>
                    </div>
                    <button type="submit" class="btn btn-success">Adicionar Placa</button>
                </form>
            </div>
        </div>
        
        <!-- Logs Recentes -->
        <div class="section">
            <div class="section-header">
                <h2>Logs de Acesso Recentes</h2>
            </div>
            <div class="section-content">
                <div id="logs-content">
                    <div class="loading">Carregando logs...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Função para carregar estatísticas
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                if (data.success) {
                    const stats = data.data;
                    document.getElementById('stat-autorizadas').textContent = stats.total_placas_autorizadas;
                    document.getElementById('stat-nao-autorizadas').textContent = stats.total_placas_nao_autorizadas;
                    document.getElementById('stat-acessos-hoje').textContent = stats.acessos_hoje;
                    document.getElementById('stat-taxa-autorizacao').textContent = stats.taxa_autorizacao_hoje.toFixed(1) + '%';
                }
            } catch (error) {
                console.error('Erro ao carregar estatísticas:', error);
            }
        }
        
        // Função para carregar logs
        async function loadLogs() {
            try {
                const response = await fetch('/api/logs?limite=10');
                const data = await response.json();
                
                if (data.success) {
                    const logs = data.data;
                    const logsContent = document.getElementById('logs-content');
                    
                    if (logs.length === 0) {
                        logsContent.innerHTML = '<p>Nenhum log encontrado.</p>';
                        return;
                    }
                    
                    let tableHTML = `
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Data/Hora</th>
                                    <th>Placa</th>
                                    <th>Status</th>
                                    <th>Ação</th>
                                    <th>Confiança</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    logs.forEach(log => {
                        const timestamp = new Date(log.timestamp).toLocaleString('pt-BR');
                        const statusBadge = log.status_validacao === 'AUTORIZADA' ? 'badge-success' : 'badge-danger';
                        const confianca = log.confianca_ocr ? (log.confianca_ocr * 100).toFixed(1) + '%' : '-';
                        
                        tableHTML += `
                            <tr>
                                <td>${timestamp}</td>
                                <td><strong>${log.placa}</strong></td>
                                <td><span class="badge ${statusBadge}">${log.status_validacao}</span></td>
                                <td>${log.acao_cancela}</td>
                                <td>${confianca}</td>
                            </tr>
                        `;
                    });
                    
                    tableHTML += '</tbody></table>';
                    logsContent.innerHTML = tableHTML;
                }
            } catch (error) {
                console.error('Erro ao carregar logs:', error);
                document.getElementById('logs-content').innerHTML = '<div class="error">Erro ao carregar logs.</div>';
            }
        }
        
        // Função para validar placa
        document.getElementById('validation-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const placa = document.getElementById('placa-input').value.trim().toUpperCase();
            const messageDiv = document.getElementById('validation-message');
            
            if (!placa) {
                messageDiv.innerHTML = '<div class="error">Por favor, digite uma placa.</div>';
                return;
            }
            
            try {
                messageDiv.innerHTML = '<div class="loading">Validando placa...</div>';
                
                const response = await fetch('/api/validate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ placa })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const result = data.data;
                    const statusClass = result.autorizada ? 'success' : 'error';
                    const statusText = result.autorizada ? 'AUTORIZADA' : 'NÃO AUTORIZADA';
                    
                    messageDiv.innerHTML = `
                        <div class="${statusClass}">
                            <strong>Placa ${placa}: ${statusText}</strong><br>
                            Status: ${result.status}<br>
                            Ação da Cancela: ${result.acao_cancela}
                        </div>
                    `;
                } else {
                    messageDiv.innerHTML = `<div class="error">Erro: ${data.error}</div>`;
                }
            } catch (error) {
                messageDiv.innerHTML = '<div class="error">Erro ao validar placa.</div>';
            }
        });
        
        // Função para adicionar placa
        document.getElementById('add-plate-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const placa = document.getElementById('nova-placa').value.trim().toUpperCase();
            const status = document.getElementById('status-placa').value;
            const modelo = document.getElementById('modelo-veiculo').value.trim();
            const cor = document.getElementById('cor-veiculo').value.trim();
            const cliente = document.getElementById('nome-cliente').value.trim();
            const messageDiv = document.getElementById('add-plate-message');
            
            if (!placa) {
                messageDiv.innerHTML = '<div class="error">Por favor, digite uma placa.</div>';
                return;
            }
            
            try {
                messageDiv.innerHTML = '<div class="loading">Adicionando placa...</div>';
                
                const response = await fetch('/api/add-plate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        placa,
                        status,
                        modelo,
                        cor,
                        cliente
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    messageDiv.innerHTML = '<div class="success">Placa adicionada com sucesso!</div>';
                    document.getElementById('add-plate-form').reset();
                    loadStats(); // Atualiza as estatísticas
                } else {
                    messageDiv.innerHTML = `<div class="error">Erro: ${data.error}</div>`;
                }
            } catch (error) {
                messageDiv.innerHTML = '<div class="error">Erro ao adicionar placa.</div>';
            }
        });
        
        // Carrega dados iniciais
        loadStats();
        loadLogs();
        
        // Atualiza dados a cada 30 segundos
        setInterval(() => {
            loadStats();
            loadLogs();
        }, 30000);
    </script>
</body>
</html>
'''

# Cria o diretório de templates se não existir
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
os.makedirs(templates_dir, exist_ok=True)

# Salva o template
with open(os.path.join(templates_dir, 'dashboard.html'), 'w', encoding='utf-8') as f:
    f.write(template_html)

if __name__ == '__main__':
    print("Iniciando interface web do sistema de cancela...")
    print("Acesse: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
