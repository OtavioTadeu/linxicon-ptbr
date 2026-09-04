import random
from sentence_transformers import util
import motor

print("Carregando o vocabulário para o gerador...")
with open('dicionario_limpo.txt', 'r', encoding='utf-8') as f:
    VOCABULARIO_BASE = [linha.strip() for linha in f]

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

def gerar_caminho(qtd_saltos=4, tolerancia=15.0):
    limite_tentativas = 1000 
    tentativas_atuais = 0

    while tentativas_atuais < limite_tentativas:
        tentativas_atuais += 1
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
            tem_atalho = False
            
            for i in range(len(caminho)):
                for j in range(i + 2, len(caminho)):
                    # 3. Lógica "Just In Time" (Sob Demanda)
                    # Calculamos o vetor APENAS para as 5 palavras sorteadas neste caminho
                    v1 = motor.modelo.encode(caminho[i])
                    v2 = motor.modelo.encode(caminho[j])
                    sim = util.cos_sim(v1, v2).item() * 100
                    
                    if sim >= tolerancia:
                        tem_atalho = True
                        break 
                if tem_atalho:
                    break
            
            if not tem_atalho:
                return caminho
                
    nova_tolerancia = tolerancia + 5.0
    print(f"Aviso: Caminho não encontrado. Afrouxando bloqueio de atalhos para {nova_tolerancia}%...")
    return gerar_caminho(qtd_saltos, nova_tolerancia)

if __name__ == "__main__":
    print("\n--- Gerador de Desafios Linxicon ---")
    caminho_gerado = gerar_caminho(qtd_saltos=4)
    
    print("\nCaminho secreto gerado pelo sistema:")
    print(" -> ".join(caminho_gerado))
    
    print(f"\nO desafio do dia para o jogador será:")
    print(f"Conecte: [{caminho_gerado[0]}] até [{caminho_gerado[-1]}]")