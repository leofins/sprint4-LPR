#!/usr/bin/env python3
"""
Interface web simples para monitoramento do sistema de cancela.
Utiliza Flask para criar uma interface de monitoramento em tempo real com CRUD completo.
"""

from flask import Flask, render_template, jsonify, request
import sys
import os
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DatabaseManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sistema_cancela_2024'
API_URL = "http://localhost:8000"
db_manager = DatabaseManager()

@app.route('/')
def index():
    return render_template('dashboard.html')

# --- ROTAS DA API ---

@app.route('/api/stats')
def get_stats():
    stats = db_manager.obter_estatisticas()
    return jsonify({'success': True, 'data': stats})

@app.route('/api/logs')
def get_logs():
    logs = db_manager.obter_logs_recentes(limite=20)
    return jsonify({'success': True, 'data': logs})

@app.route('/api/placas')
def get_placas():
    # CORREÇÃO: Chama o novo método para listar TODAS as placas
    placas = db_manager.listar_todas_as_placas()
    return jsonify({'success': True, 'data': placas})

@app.route('/api/add-plate', methods=['POST'])
def add_plate():
    data = request.get_json()
    sucesso = db_manager.adicionar_placa(
        placa=data.get('placa', '').strip().upper(), status=data.get('status'),
        veiculo_modelo=data.get('modelo'), veiculo_cor=data.get('cor'),
        cliente_nome=data.get('cliente')
    )
    if sucesso: return jsonify({'success': True, 'message': 'Placa adicionada com sucesso'})
    return jsonify({'success': False, 'error': 'Placa já existe no sistema'}), 409

@app.route('/api/update-plate/<placa>', methods=['PUT'])
def update_plate(placa):
    data = request.get_json()
    sucesso = db_manager.atualizar_placa(
        placa=placa, status=data.get('status'),
        veiculo_modelo=data.get('modelo'), veiculo_cor=data.get('cor'),
        cliente_nome=data.get('cliente')
    )
    if sucesso: return jsonify({'success': True, 'message': 'Placa atualizada com sucesso'})
    return jsonify({'success': False, 'error': 'Falha ao atualizar a placa'}), 500

@app.route('/api/delete-plate/<placa>', methods=['DELETE'])
def delete_plate(placa):
    sucesso = db_manager.remover_placa(placa)
    if sucesso: return jsonify({'success': True, 'message': 'Placa removida com sucesso'})
    return jsonify({'success': False, 'error': 'Falha ao remover a placa'}), 500

# --- TEMPLATE HTML COMPLETO E CORRIGIDO ---
template_html = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Cancela - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background-color: #f5f5f5; color: #333; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header h1 { font-size: 2rem; }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .stat-card h3 { color: #667eea; font-size: 2rem; margin-bottom: 0.5rem; }
        .section { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; overflow: hidden; }
        .section-header { background: #f8f9fa; padding: 1rem 1.5rem; border-bottom: 1px solid #e9ecef; }
        .section-header h2 { color: #495057; font-size: 1.2rem; }
        .section-content { padding: 1.5rem; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        .form-group input, .form-group select { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 5px; font-size: 1rem; }
        .btn { color: white; padding: 0.5rem 1rem; border: none; border-radius: 5px; cursor: pointer; font-size: 0.9rem; transition: background 0.3s; margin-right: 0.5rem;}
        .btn:hover { opacity: 0.9; }
        .btn-success { background: #28a745; }
        .btn-warning { background: #ffc107; }
        .btn-danger { background: #dc3545; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #e9ecef; }
        .badge { padding: 0.25rem 0.5rem; border-radius: 20px; font-size: 0.8rem; font-weight: 500; color: white; }
        .badge-success { background: #28a745; }
        .badge-danger { background: #dc3545; }
        .message { padding: 1rem; border-radius: 5px; margin-bottom: 1rem; }
        .error { background: #f8d7da; color: #721c24; }
        .success { background: #d4edda; color: #155724; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: #fefefe; margin: 10% auto; padding: 20px; border: 1px solid #888; width: 80%; max-width: 500px; border-radius: 10px; }
        .close-btn { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header"><h1>Sistema de Cancela</h1><p>Dashboard de Monitoramento e Controle</p></div>
    <div class="container">
        <div class="stats-grid" id="stats-grid">
            <div class="stat-card"><h3 id="stat-autorizadas">-</h3><p>Placas Autorizadas</p></div>
            <div class="stat-card"><h3 id="stat-nao-autorizadas">-</h3><p>Placas Não Autorizadas</p></div>
            <div class="stat-card"><h3 id="stat-acessos-hoje">-</h3><p>Acessos Hoje</p></div>
            <div class="stat-card"><h3 id="stat-taxa-autorizacao">-</h3><p>Taxa de Autorização</p></div>
        </div>
        
        <div class="section">
            <div class="section-header"><h2>Gerenciamento de Placas</h2></div>
            <div class="section-content">
                <div id="plates-message"></div>
                <div id="plates-list-content" style="max-height: 400px; overflow-y: auto;"></div>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>Adicionar Nova Placa</h2></div>
            <div class="section-content">
                <div id="add-plate-message"></div>
                <form id="add-plate-form">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                        <div class="form-group"><label for="nova-placa">Placa:</label><input type="text" id="nova-placa" required style="text-transform: uppercase;"></div>
                        <div class="form-group"><label for="status-placa">Status:</label><select id="status-placa" required><option value="AUTORIZADA">Autorizada</option><option value="NAO_AUTORIZADA">Não Autorizada</option></select></div>
                        <div class="form-group"><label for="modelo-veiculo">Modelo:</label><input type="text" id="modelo-veiculo"></div>
                        <div class="form-group"><label for="cor-veiculo">Cor:</label><input type="text" id="cor-veiculo"></div>
                        <div class="form-group"><label for="nome-cliente">Cliente:</label><input type="text" id="nome-cliente"></div>
                    </div>
                    <button type="submit" class="btn btn-success">Adicionar Placa</button>
                </form>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>Logs de Acesso Recentes</h2></div>
            <div class="section-content"><div id="logs-content"></div></div>
        </div>
    </div>

    <div id="edit-modal" class="modal">
        <div class="modal-content">
            <span class="close-btn">&times;</span>
            <h2>Editar Placa</h2>
            <div id="edit-plate-message"></div>
            <form id="edit-plate-form">
                <input type="hidden" id="edit-placa-original">
                <div class="form-group"><label>Placa:</label><input type="text" id="edit-placa" disabled class="form-control-plaintext"></div>
                <div class="form-group"><label for="edit-status">Status:</label><select id="edit-status" required><option value="AUTORIZADA">Autorizada</option><option value="NAO_AUTORIZADA">Não Autorizada</option></select></div>
                <div class="form-group"><label for="edit-modelo">Modelo:</label><input type="text" id="edit-modelo"></div>
                <div class="form-group"><label for="edit-cor">Cor:</label><input type="text" id="edit-cor"></div>
                <div class="form-group"><label for="edit-cliente">Cliente:</label><input type="text" id="edit-cliente"></div>
                <button type="submit" class="btn btn-success">Salvar Alterações</button>
            </form>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            loadAllData();
            setupEventListeners();
        });
        setInterval(loadAllData, 30000);

        function loadAllData() {
            loadStats();
            loadLogs();
            loadPlates();
        }

        async function loadStats() {
            const result = await fetch('/api/stats').then(res => res.json());
            if(result.success) {
                document.getElementById('stat-autorizadas').textContent = result.data.total_placas_autorizadas;
                document.getElementById('stat-nao-autorizadas').textContent = result.data.total_placas_nao_autorizadas;
                document.getElementById('stat-acessos-hoje').textContent = result.data.acessos_hoje;
                document.getElementById('stat-taxa-autorizacao').textContent = result.data.taxa_autorizacao_hoje.toFixed(1) + '%';
            }
        }
        
        async function loadLogs() {
            const result = await fetch('/api/logs').then(res => res.json());
            if(result.success) {
                const logs = result.data;
                const container = document.getElementById('logs-content');
                if (logs.length === 0) { container.innerHTML = '<p>Nenhum log encontrado.</p>'; return; }
                let table = '<table class="table"><thead><tr><th>Data/Hora</th><th>Placa</th><th>Status</th><th>Ação</th><th>Confiança</th></tr></thead><tbody>';
                logs.forEach(log => {
                    table += `<tr><td>${new Date(log.timestamp).toLocaleString('pt-BR')}</td><td><strong>${log.placa}</strong></td><td>${log.status_validacao}</td><td>${log.acao_cancela}</td><td>${log.confianca_ocr ? (log.confianca_ocr * 100).toFixed(1) + '%' : '-'}</td></tr>`;
                });
                container.innerHTML = table + '</tbody></table>';
            }
        }

        async function loadPlates() {
            const result = await fetch('/api/placas').then(res => res.json());
            const container = document.getElementById('plates-list-content');
            if(result.success) {
                const plates = result.data;
                if (plates.length === 0) { container.innerHTML = '<p>Nenhuma placa cadastrada.</p>'; return; }
                let table = '<table class="table"><thead><tr><th>Placa</th><th>Status</th><th>Modelo</th><th>Cor</th><th>Cliente</th><th>Ações</th></tr></thead><tbody>';
                plates.forEach(p => {
                    const statusBadge = p.status === 'AUTORIZADA' ? 'badge-success' : 'badge-danger';
                    table += `<tr><td><strong>${p.placa}</strong></td><td><span class="badge ${statusBadge}">${p.status.replace('_', ' ')}</span></td><td>${p.veiculo_modelo || '-'}</td><td>${p.veiculo_cor || '-'}</td><td>${p.cliente_nome || '-'}</td><td><button class="btn btn-warning" onclick='openEditModal(${JSON.stringify(p)})'>Editar</button><button class="btn btn-danger" onclick="deletePlate('${p.placa}')">Remover</button></td></tr>`;
                });
                container.innerHTML = table + '</tbody></table>';
            } else { container.innerHTML = '<div class="message error">Erro ao carregar placas.</div>';}
        }
        
        const modal = document.getElementById('edit-modal');
        function openEditModal(plateData) {
            document.getElementById('edit-plate-message').innerHTML = '';
            document.getElementById('edit-placa-original').value = plateData.placa;
            document.getElementById('edit-placa').value = plateData.placa;
            document.getElementById('edit-status').value = plateData.status;
            document.getElementById('edit-modelo').value = plateData.veiculo_modelo || '';
            document.getElementById('edit-cor').value = plateData.veiculo_cor || '';
            document.getElementById('edit-cliente').value = plateData.cliente_nome || '';
            modal.style.display = 'block';
        }

        async function deletePlate(placa) {
            if (!confirm(`Tem certeza que deseja remover a placa ${placa}?`)) return;
            const response = await fetch(`/api/delete-plate/${placa}`, { method: 'DELETE' });
            const result = await response.json();
            showMessage('plates-message', result.success, result.success ? 'Placa removida com sucesso!' : result.error);
            if(result.success) loadAllData();
        }
        
        function showMessage(elementId, success, message) {
            const div = document.getElementById(elementId);
            div.className = `message ${success ? 'success' : 'error'}`;
            div.textContent = message;
            setTimeout(() => div.innerHTML = '', 4000);
        }

        function setupEventListeners() {
            document.querySelector('.close-btn').onclick = () => { modal.style.display = 'none'; };
            window.onclick = (event) => { if (event.target == modal) { modal.style.display = 'none'; } };
            
            document.getElementById('add-plate-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const form = e.target;
                const payload = {
                    placa: form.querySelector('#nova-placa').value, status: form.querySelector('#status-placa').value,
                    modelo: form.querySelector('#modelo-veiculo').value, cor: form.querySelector('#cor-veiculo').value,
                    cliente: form.querySelector('#nome-cliente').value
                };
                const response = await fetch('/api/add-plate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const result = await response.json();
                showMessage('add-plate-message', result.success, result.success ? 'Placa adicionada com sucesso!' : result.error);
                if (result.success) { form.reset(); loadAllData(); }
            });

            document.getElementById('edit-plate-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const originalPlaca = document.getElementById('edit-placa-original').value;
                const payload = {
                    status: document.getElementById('edit-status').value, modelo: document.getElementById('edit-modelo').value,
                    cor: document.getElementById('edit-cor').value, cliente: document.getElementById('edit-cliente').value,
                };
                const response = await fetch(`/api/update-plate/${originalPlaca}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const result = await response.json();
                showMessage('edit-plate-message', result.success, result.success ? 'Placa atualizada com sucesso!' : result.error);
                if (result.success) { setTimeout(() => { modal.style.display = 'none'; loadAllData(); }, 1500); }
            });
        }
    </script>
</body>
</html>
'''

templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
os.makedirs(templates_dir, exist_ok=True)
with open(os.path.join(templates_dir, 'dashboard.html'), 'w', encoding='utf-8') as f:
    f.write(template_html)

if __name__ == '__main__':
    print("Iniciando interface web do sistema de cancela...")
    print("Acesse: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)