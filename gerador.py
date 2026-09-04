import random
from sentence_transformers import util
import motor

CONCEITOS_BASE = [
    "tempo", "espaço", "vida", "morte", "fogo", "água", "terra", "ar",
    "luz", "sombra", "sol", "lua", "estrela", "planeta", "animal", "planta",
    "homem", "mulher", "criança", "velho", "amor", "ódio", "paz", "guerra",
    "cidade", "floresta", "oceano", "deserto", "montanha", "vale", "pedra",
    "ciência", "magia", "tecnologia", "natureza", "mente", "corpo", "alma",
    "sonho", "realidade", "passado", "futuro", "verdade", "mentira", "chuva",
    "rei", "escravo", "deus", "humano", "frio", "calor", "dia", "noite",
    "viagem", "casa", "caminho", "destino", "início", "fim", "som", "silêncio"
]

print("Calculando IA para os conceitos base...")
CACHE_VETORES = {p: motor.modelo.encode(p) for p in CONCEITOS_BASE}

LIMITE_CONEXAO = 50.0 

def buscar_proxima_palavra(palavra_atual, caminho_atual):
    vetor_atual = CACHE_VETORES[palavra_atual]
    opcoes = list(CONCEITOS_BASE)
    random.shuffle(opcoes)
    
    for candidata in opcoes:
        if candidata in caminho_atual:
            continue
            
        vetor_candidata = CACHE_VETORES[candidata]
        similaridade = util.cos_sim(vetor_atual, vetor_candidata).item() * 100

        if LIMITE_CONEXAO <= similaridade <= 75.0:
            return candidata, similaridade
            
    return None, 0

def gerar_caminho(qtd_saltos=3, tolerancia_inicial=15.0):

    tolerancia_maxima = LIMITE_CONEXAO - 1.0 
    tolerancia_atual = tolerancia_inicial
    
    limite_tentativas = 500
    tentativas_atuais = 0

    while tentativas_atuais < limite_tentativas:
        tentativas_atuais += 1
        palavra_inicial = random.choice(CONCEITOS_BASE)
        caminho = [palavra_inicial]
        
        for _ in range(qtd_saltos):
            palavra_atual = caminho[-1]
            proxima, _ = buscar_proxima_palavra(palavra_atual, caminho)
            if proxima:
                caminho.append(proxima)
            else:
                break
                
        if len(caminho) == qtd_saltos + 1:
            tem_atalho = False
            
            for i in range(len(caminho)):
                for j in range(i + 2, len(caminho)):
                    v1 = CACHE_VETORES[caminho[i]]
                    v2 = CACHE_VETORES[caminho[j]]
                    sim = util.cos_sim(v1, v2).item() * 100
                    
                    if sim >= tolerancia_atual:
                        tem_atalho = True
                        break 
                if tem_atalho:
                    break
            
            if not tem_atalho:
                return caminho
                
    if tolerancia_atual < tolerancia_maxima:
        nova_tolerancia = min(tolerancia_atual + 5.0, tolerancia_maxima)
        print(f"Afrouxando bloqueio de atalhos para {nova_tolerancia}%...")
        return gerar_caminho(qtd_saltos, nova_tolerancia)
        
    print("Caminho ideal muito rígido. Reduzindo para 2 saltos complexos.")
    return gerar_caminho(qtd_saltos=2, tolerancia_inicial=20.0)