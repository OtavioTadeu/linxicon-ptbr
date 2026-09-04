from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

class Tentativa(BaseModel):
    palavra_alvo: str
    palavra_jogada: str

@app.post("/validar-conexao")
def validar_conexao(tentativa: Tentativa):
    p1 = tentativa.palavra_alvo.lower().strip()
    p2 = tentativa.palavra_jogada.lower().strip()

    if not motor.eh_palavra_valida(p1) or not motor.eh_palavra_valida(p2):
        raise HTTPException(status_code=400, detail="Palavra não reconhecida no vocabulário em português.")

    porcentagem = motor.calcular_similaridade(p1, p2)
    
    return {
        "palavra_alvo": p1,
        "palavra_jogada": p2,
        "similaridade": round(porcentagem, 1),
        "conectou": porcentagem >= 50.0
    }

@app.get("/desafio-diario")
def obter_desafio_diario():
    caminho = gerador.gerar_caminho(qtd_saltos=4)
    
    return {
        "palavra_inicial": caminho[0],
        "palavra_final": caminho[-1],
        "saltos_minimos": 4,
        "caminho_secreto": caminho
    }