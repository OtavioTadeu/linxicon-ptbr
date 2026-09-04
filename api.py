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

class Tentativa(BaseModel):
    palavra_alvo: str
    palavra_jogada: str
    session_id: str | None = None
    palavras_existentes: list[str] | None = None

class ConfirmarPalavra(BaseModel):
    session_id: str
    palavra: str

@app.get("/config")
async def obter_config():
    return {
        "threshold": motor.THRESHOLD
    }

@app.post("/validar-conexao")
async def validar_conexao(tentativa: Tentativa):
    p1 = tentativa.palavra_alvo.lower().strip()
    p2 = tentativa.palavra_jogada.lower().strip()

    # #16 Validação de duplicatas: palavra jogada não pode ser igual à palavra alvo
    if p1 == p2:
        raise HTTPException(
            status_code=400,
            detail="Palavra duplicada: a palavra jogada não pode ser igual à palavra alvo."
        )

    # #16 Validação de duplicatas: verificar contra palavras existentes no grafo fornecidas na requisição
    if tentativa.palavras_existentes:
        existentes = {p.lower().strip() for p in tentativa.palavras_existentes}
        if p2 in existentes:
            raise HTTPException(
                status_code=400,
                detail=f"Palavra duplicada: '{p2}' já existe no grafo atual."
            )

    # #16 Validação de duplicatas: verificar contra sessão ativa no backend
    if tentativa.session_id:
        sessao = sessoes.get(tentativa.session_id)
        if sessao and p2 in sessao.get("palavras", set()):
            raise HTTPException(
                status_code=400,
                detail=f"Palavra duplicada: '{p2}' já foi utilizada nesta sessão."
            )

    # #19 Verificação de palavras válidas assíncrona (threadpool)
    p1_valida = await asyncio.to_thread(motor.eh_palavra_valida, p1)
    p2_valida = await asyncio.to_thread(motor.eh_palavra_valida, p2)

    if not p1_valida or not p2_valida:
        invalida = p1 if not p1_valida else p2
        raise HTTPException(
            status_code=400,
            detail=f"Palavra '{invalida}' não reconhecida no vocabulário em português."
        )

    # #19 Cálculo de similaridade assíncrono via threadpool (não bloqueia event loop)
    porcentagem = await asyncio.to_thread(motor.calcular_similaridade, p1, p2)
    
    return {
        "palavra_alvo": p1,
        "palavra_jogada": p2,
        "similaridade": round(porcentagem, 1),
        "conectou": porcentagem >= motor.THRESHOLD,
        "feedback": motor.classificar_feedback(porcentagem)
    }

@app.post("/confirmar-palavra")
async def confirmar_palavra(payload: ConfirmarPalavra):
    """#16: Confirma e registra uma palavra conectada no histórico da sessão."""
    sid = payload.session_id
    if sid not in sessoes:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    
    palavra = payload.palavra.lower().strip()
    sessoes[sid]["palavras"].add(palavra)
    return {
        "session_id": sid,
        "palavras_registradas": list(sessoes[sid]["palavras"])
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