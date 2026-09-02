from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import motor  # Importa a inteligência que já construímos

app = FastAPI(title="Linxicon PT-BR API")

# Define o formato exato do JSON que o front-end vai nos enviar
class Tentativa(BaseModel):
    palavra_alvo: str
    palavra_jogada: str

@app.post("/validar-conexao")
def validar_conexao(tentativa: Tentativa):
    p1 = tentativa.palavra_alvo.lower().strip()
    p2 = tentativa.palavra_jogada.lower().strip()

    # O nosso "Porteiro" em ação
    if not motor.eh_palavra_valida(p1) or not motor.eh_palavra_valida(p2):
        raise HTTPException(status_code=400, detail="Palavra não reconhecida no vocabulário em português.")

    # O Motor Semântico calculando a distância vetorial
    porcentagem = motor.calcular_similaridade(p1, p2)
    
    return {
        "palavra_alvo": p1,
        "palavra_jogada": p2,
        "similaridade": round(porcentagem, 1),
        "conectou": porcentagem >= 40.0
    }