import asyncio
import time
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import motor
import gerador

app = FastAPI(title="Linxicon PT-BR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# #16: Gerenciamento de sessões para controle de duplicatas no backend
sessoes: dict[str, dict] = {}

def limpar_sessoes_antigas():
    agora = time.time()
    limite = agora - 86400  # 24 horas
    chaves = [sid for sid, dados in sessoes.items() if dados.get("criado_em", agora) < limite]
    for sid in chaves:
        sessoes.pop(sid, None)

class TentativaBatch(BaseModel):
    palavra_jogada: str
    palavras_existentes: list[str]
    session_id: str | None = None

@app.get("/config")
async def obter_config():
    return {
        "threshold": motor.THRESHOLD
    }

@app.post("/validar-todas")
async def validar_todas(tentativa: TentativaBatch):
    """Valida a palavra jogada contra todas as palavras do grafo em uma única requisição."""
    palavra = tentativa.palavra_jogada.lower().strip()

    # Validação de duplicatas contra palavras existentes no grafo
    existentes = {p.lower().strip() for p in tentativa.palavras_existentes}
    if palavra in existentes:
        raise HTTPException(
            status_code=400,
            detail=f"Palavra duplicada: '{palavra}' já existe no grafo atual."
        )

    # Validação de duplicatas contra sessão ativa no backend
    if tentativa.session_id:
        sessao = sessoes.get(tentativa.session_id)
        if sessao and palavra in sessao.get("palavras", set()):
            raise HTTPException(
                status_code=400,
                detail=f"Palavra duplicada: '{palavra}' já foi utilizada nesta sessão."
            )

    # Verificação de palavra válida (threadpool)
    palavra_valida = await asyncio.to_thread(motor.eh_palavra_valida, palavra)
    if not palavra_valida:
        raise HTTPException(
            status_code=400,
            detail=f"Palavra '{palavra}' não reconhecida no vocabulário em português."
        )

    # Cálculo de similaridades em batch (threadpool — codifica a palavra uma única vez)
    alvos = [p.lower().strip() for p in tentativa.palavras_existentes]
    resultados = await asyncio.to_thread(motor.calcular_similaridades_batch, palavra, alvos)

    # Registrar palavra na sessão automaticamente
    if tentativa.session_id and tentativa.session_id in sessoes:
        sessoes[tentativa.session_id]["palavras"].add(palavra)

    return {
        "palavra_jogada": palavra,
        "resultados": resultados
    }

@app.get("/desafio-diario")
async def obter_desafio_diario():
    limpar_sessoes_antigas()
    # #19 Geração assíncrona em threadpool
    caminho = await asyncio.to_thread(gerador.gerar_desafio_diario, 4)
    
    print(f"[DEBUG] Desafio diário: {caminho}")

    # #16 Criar sessão para rastreamento de palavras
    session_id = uuid4().hex
    sessoes[session_id] = {
        "palavras": {caminho[0], caminho[-1]},
        "criado_em": time.time(),
        "modo": "diario"
    }

    return {
        "session_id": session_id,
        "palavra_inicial": caminho[0],
        "palavra_final": caminho[-1],
        "saltos_minimos": 4
    }

@app.get("/pratica")
async def obter_pratica():
    limpar_sessoes_antigas()
    # #19 Geração assíncrona em threadpool
    caminho = await asyncio.to_thread(gerador.gerar_pratica, 4)
    
    print(f"[DEBUG] Prática: {caminho}")

    # #16 Criar sessão para rastreamento de palavras
    session_id = uuid4().hex
    sessoes[session_id] = {
        "palavras": {caminho[0], caminho[-1]},
        "criado_em": time.time(),
        "modo": "pratica"
    }

    return {
        "session_id": session_id,
        "palavra_inicial": caminho[0],
        "palavra_final": caminho[-1],
        "saltos_minimos": 4
    }

# Servir o frontend (index.html na raiz, outros estáticos)
@app.get("/")
async def servir_index():
    return FileResponse("static/index.html")

app.mount("/", StaticFiles(directory="static"), name="static")