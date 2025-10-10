#!/usr/bin/env python3
"""
API FastAPI para validação de placas no sistema de cancela.
Fornece endpoints para verificar placas autorizadas e gerenciar o sistema.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import sys
import os
from datetime import datetime

# Adiciona o diretório pai ao path para importar o módulo database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="Sistema de Cancela - API de Validação de Placas",
    description="API para validação de placas de veículos em sistema de cancela automatizada",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS para permitir acesso de diferentes origens
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância global do gerenciador de banco de dados
db_manager = DatabaseManager()


# Modelos Pydantic para validação de dados

class PlacaRequest(BaseModel):
    """Modelo para requisição de validação de placa."""
    placa: str = Field(..., min_length=7, max_length=8, description="Placa do veículo")
    confianca_ocr: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confiança do OCR (0.0 a 1.0)")


class PlacaResponse(BaseModel):
    """Modelo para resposta de validação de placa."""
    placa: str
    autorizada: bool
    status: str
    acao_cancela: str
    timestamp: str
    dados_veiculo: Optional[Dict] = None
    log_id: Optional[int] = None


class NovaPlacaRequest(BaseModel):
    """Modelo para adicionar nova placa."""
    placa: str = Field(..., min_length=7, max_length=8)
    status: str = Field(..., pattern="^(AUTORIZADA|NAO_AUTORIZADA)$")
    veiculo_modelo: Optional[str] = None
    veiculo_cor: Optional[str] = None
    cliente_nome: Optional[str] = None


class AtualizarStatusRequest(BaseModel):
    """Modelo para atualizar status de placa."""
    status: str = Field(..., pattern="^(AUTORIZADA|NAO_AUTORIZADA)$")


# Endpoints da API

@app.get("/", tags=["Sistema"])
async def root():
    """Endpoint raiz da API."""
    return {
        "message": "Sistema de Cancela - API de Validação de Placas",
        "version": "1.0.0",
        "status": "ativo",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["Sistema"])
async def health_check():
    """Endpoint para verificação de saúde da API."""
    try:
        # Testa a conexão com o banco de dados
        stats = db_manager.obter_estatisticas()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro na conexão com o banco de dados: {str(e)}"
        )


@app.post("/validar-placa", response_model=PlacaResponse, tags=["Validação"])
async def validar_placa(request: PlacaRequest):
    """
    Valida uma placa de veículo e determina se a cancela deve ser aberta.

    Args:
        request: Dados da placa a ser validada.

    Returns:
        Resposta com o status de autorização e ação da cancela.
    """
    try:
        # Verifica a placa no banco de dados
        resultado = db_manager.verificar_placa_autorizada(request.placa)

        # Determina a ação da cancela
        acao_cancela = "ABERTA" if resultado['autorizada'] else "FECHADA"

        # Registra o log de acesso
        log_id = db_manager.registrar_log_acesso(
            placa=request.placa,
            status_validacao=resultado['status'],
            acao_cancela=acao_cancela,
            confianca_ocr=request.confianca_ocr,
            observacoes=f"Validação via API - Confiança OCR: {request.confianca_ocr}"
        )

        return PlacaResponse(
            placa=request.placa.upper(),
            autorizada=resultado['autorizada'],
            status=resultado['status'],
            acao_cancela=acao_cancela,
            timestamp=datetime.now().isoformat(),
            dados_veiculo=resultado['dados'],
            log_id=log_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@app.get("/placas-autorizadas", tags=["Gerenciamento"])
async def listar_placas_autorizadas():
    """Lista todas as placas autorizadas."""
    try:
        placas = db_manager.listar_placas_autorizadas()
        return {
            "total": len(placas),
            "placas": placas
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar placas: {str(e)}"
        )


@app.post("/placas", tags=["Gerenciamento"])
async def adicionar_placa(request: NovaPlacaRequest):
    """Adiciona uma nova placa ao sistema."""
    try:
        sucesso = db_manager.adicionar_placa(
            placa=request.placa,
            status=request.status,
            veiculo_modelo=request.veiculo_modelo,
            veiculo_cor=request.veiculo_cor,
            cliente_nome=request.cliente_nome
        )

        if sucesso:
            return {
                "message": "Placa adicionada com sucesso",
                "placa": request.placa.upper(),
                "status": request.status
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Placa já existe no sistema"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao adicionar placa: {str(e)}"
        )


@app.put("/placas/{placa}/status", tags=["Gerenciamento"])
async def atualizar_status_placa(placa: str, request: AtualizarStatusRequest):
    """Atualiza o status de uma placa existente."""
    try:
        sucesso = db_manager.atualizar_status_placa(placa, request.status)

        if sucesso:
            return {
                "message": "Status da placa atualizado com sucesso",
                "placa": placa.upper(),
                "novo_status": request.status
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Placa não encontrada"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar status da placa: {str(e)}"
        )


@app.get("/logs", tags=["Monitoramento"])
async def obter_logs_recentes(limite: int = 50):
    """Obtém os logs de acesso mais recentes."""
    try:
        if limite > 200:
            limite = 200  # Limita para evitar sobrecarga

        logs = db_manager.obter_logs_recentes(limite)
        return {
            "total": len(logs),
            "limite": limite,
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter logs: {str(e)}"
        )


@app.get("/estatisticas", tags=["Monitoramento"])
async def obter_estatisticas():
    """Obtém estatísticas do sistema."""
    try:
        stats = db_manager.obter_estatisticas()
        return {
            "timestamp": datetime.now().isoformat(),
            "estatisticas": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )


# Manipulador de exceções global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manipulador global de exceções."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Erro interno do servidor",
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn

    print("Iniciando API do Sistema de Cancela...")
    print("Documentação disponível em: http://localhost:8000/docs")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

