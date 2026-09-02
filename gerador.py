import random
from sentence_transformers import SentenceTransformer, util

print("Carregando modelo e gerando cache de vetores (Isso pode levar alguns segundos)...")
modelo = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

VOCABULARIO_BASE = [
    "fogo", "calor", "sol", "verão", "praia", "areia", "mar", "oceano", 
    "água", "chuva", "nuvem", "céu", "pássaro", "asa", "avião", "viagem", 
    "carro", "roda", "estrada", "caminho", "floresta", "árvore", "folha",
    "terra", "planeta", "espaço", "estrela", "luz", "dia", "noite"
]

CACHE_VETORES = {palavra: modelo.encode(palavra) for palavra in VOCABULARIO_BASE}

def buscar_proxima_palavra(palavra_atual, caminho_atual):
    """Busca uma palavra no vocabulário que tenha >= 40% de similaridade, mas que não esteja no caminho."""
    vetor_atual = CACHE_VETORES[palavra_atual]
    
    opcoes = list(VOCABULARIO_BASE)
    random.shuffle(opcoes)
    
    for candidata in opcoes:
        if candidata in caminho_atual:
            continue
            
        vetor_candidata = CACHE_VETORES[candidata]
        similaridade = util.cos_sim(vetor_atual, vetor_candidata).item() * 100
        
        if similaridade >= 40.0:
            return candidata, similaridade
            
    return None, 0

def gerar_caminho(qtd_saltos=4):
    while True:
        palavra_inicial = random.choice(VOCABULARIO_BASE)
        caminho = [palavra_inicial]
        
        for _ in range(qtd_saltos):
            palavra_atual = caminho[-1]
            proxima, _ = buscar_proxima_palavra(palavra_atual, caminho)
            
            if proxima:
                caminho.append(proxima)
            else:
                break
                
        if len(caminho) == qtd_saltos + 1:
            return caminho

if __name__ == "__main__":
    print("\n--- Gerador de Desafios Linxicon ---")
    caminho_gerado = gerar_caminho(qtd_saltos=4)
    
    print("\nCaminho secreto gerado pelo sistema:")
    print(" -> ".join(caminho_gerado))
    
    print(f"\nO desafio do dia para o jogador será:")
    print(f"Conecte: [{caminho_gerado[0]}] até [{caminho_gerado[-1]}]")