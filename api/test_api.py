#!/usr/bin/env python3
"""
Script de teste para a API do sistema de cancela.
Testa os principais endpoints da API.
"""

import requests
import json
from typing import Dict, Any

class APITester:
    """Classe para testar a API do sistema de cancela."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Inicializa o testador da API.
        
        Args:
            base_url: URL base da API.
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health_check(self) -> bool:
        """Testa o endpoint de health check."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print("✅ Health check: OK")
                print(f"   Status: {data.get('status')}")
                print(f"   Database: {data.get('database')}")
                return True
            else:
                print(f"❌ Health check falhou: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro no health check: {e}")
            return False
    
    def test_validar_placa(self, placa: str, confianca_ocr: float = 0.95) -> Dict[str, Any]:
        """
        Testa a validação de uma placa.
        
        Args:
            placa: Placa a ser testada.
            confianca_ocr: Confiança do OCR.
            
        Returns:
            Resposta da API.
        """
        try:
            payload = {
                "placa": placa,
                "confianca_ocr": confianca_ocr
            }
            
            response = self.session.post(
                f"{self.base_url}/validar-placa",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                status_icon = "✅" if data['autorizada'] else "❌"
                print(f"{status_icon} Placa {placa}: {data['status']} - Cancela: {data['acao_cancela']}")
                return data
            else:
                print(f"❌ Erro ao validar placa {placa}: {response.status_code}")
                print(f"   Resposta: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Erro ao validar placa {placa}: {e}")
            return {}
    
    def test_listar_placas_autorizadas(self) -> bool:
        """Testa a listagem de placas autorizadas."""
        try:
            response = self.session.get(f"{self.base_url}/placas-autorizadas")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Placas autorizadas: {data['total']} encontradas")
                for placa in data['placas'][:3]:  # Mostra apenas as 3 primeiras
                    print(f"   - {placa['placa']}: {placa['cliente_nome']} ({placa['veiculo_modelo']})")
                if data['total'] > 3:
                    print(f"   ... e mais {data['total'] - 3} placas")
                return True
            else:
                print(f"❌ Erro ao listar placas: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao listar placas: {e}")
            return False
    
    def test_adicionar_placa(self, placa: str, status: str = "AUTORIZADA") -> bool:
        """
        Testa a adição de uma nova placa.
        
        Args:
            placa: Placa a ser adicionada.
            status: Status da placa.
            
        Returns:
            True se a placa foi adicionada com sucesso.
        """
        try:
            payload = {
                "placa": placa,
                "status": status,
                "veiculo_modelo": "Teste Model",
                "veiculo_cor": "Teste Cor",
                "cliente_nome": "Cliente Teste"
            }
            
            response = self.session.post(
                f"{self.base_url}/placas",
                json=payload
            )
            
            if response.status_code == 200:
                print(f"✅ Placa {placa} adicionada com sucesso")
                return True
            elif response.status_code == 409:
                print(f"⚠️  Placa {placa} já existe no sistema")
                return True  # Considera sucesso pois a placa existe
            else:
                print(f"❌ Erro ao adicionar placa {placa}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao adicionar placa {placa}: {e}")
            return False
    
    def test_obter_estatisticas(self) -> bool:
        """Testa a obtenção de estatísticas."""
        try:
            response = self.session.get(f"{self.base_url}/estatisticas")
            if response.status_code == 200:
                data = response.json()
                stats = data['estatisticas']
                print("✅ Estatísticas do sistema:")
                print(f"   - Placas autorizadas: {stats['total_placas_autorizadas']}")
                print(f"   - Placas não autorizadas: {stats['total_placas_nao_autorizadas']}")
                print(f"   - Acessos hoje: {stats['acessos_hoje']}")
                print(f"   - Acessos autorizados hoje: {stats['acessos_autorizados_hoje']}")
                print(f"   - Taxa de autorização hoje: {stats['taxa_autorizacao_hoje']:.1f}%")
                return True
            else:
                print(f"❌ Erro ao obter estatísticas: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return False
    
    def run_all_tests(self):
        """Executa todos os testes."""
        print("🚀 Iniciando testes da API do Sistema de Cancela")
        print("=" * 60)
        
        # Teste 1: Health check
        print("\n1. Testando health check...")
        health_ok = self.test_health_check()
        
        if not health_ok:
            print("❌ API não está funcionando. Verifique se está rodando.")
            return
        
        # Teste 2: Listar placas autorizadas
        print("\n2. Testando listagem de placas autorizadas...")
        self.test_listar_placas_autorizadas()
        
        # Teste 3: Validar placas existentes
        print("\n3. Testando validação de placas...")
        placas_teste = ["ABC1234", "DEF5678", "XYZ9999"]  # Última não existe
        
        for placa in placas_teste:
            self.test_validar_placa(placa)
        
        # Teste 4: Adicionar nova placa de teste
        print("\n4. Testando adição de nova placa...")
        self.test_adicionar_placa("TST1234", "AUTORIZADA")
        
        # Teste 5: Validar a placa recém-adicionada
        print("\n5. Testando validação da placa recém-adicionada...")
        self.test_validar_placa("TST1234")
        
        # Teste 6: Obter estatísticas
        print("\n6. Testando obtenção de estatísticas...")
        self.test_obter_estatisticas()
        
        print("\n" + "=" * 60)
        print("✅ Testes concluídos!")

def main():
    """Função principal para executar os testes."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Testa a API do sistema de cancela")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="URL base da API (padrão: http://localhost:8000)"
    )
    parser.add_argument(
        "--placa",
        help="Testa uma placa específica"
    )
    
    args = parser.parse_args()
    
    tester = APITester(args.url)
    
    if args.placa:
        print(f"Testando placa específica: {args.placa}")
        tester.test_validar_placa(args.placa)
    else:
        tester.run_all_tests()

if __name__ == "__main__":
    main()
