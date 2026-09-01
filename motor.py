from sentence_transformers import SentenceTransformer, util

# Carrega o modelo otimizado para múltiplos idiomas (incluindo Português)
print("Carregando o modelo (isso pode demorar na primeira execução)...")
modelo = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def calcular_similaridade(palavra1, palavra2):
    # Converte as palavras em vetores de significado
    vetor1 = modelo.encode(palavra1)
    vetor2 = modelo.encode(palavra2)
    
    # Calcula a similaridade de cossenos (distância semântica)
    similaridade = util.cos_sim(vetor1, vetor2).item()
    
    # Retorna o valor em porcentagem
    return similaridade * 100

if __name__ == "__main__":
    print("\n--- Validador Semântico ---")
    p1 = input("Digite a primeira palavra: ").strip().lower()
    p2 = input("Digite a segunda palavra: ").strip().lower()
    
    porcentagem = calcular_similaridade(p1, p2)
    
    print(f"\nA similaridade entre '{p1}' e '{p2}' é de {porcentagem:.1f}%")
    
    if porcentagem >= 40.0:
        print("Veredito: SUCESSO! As bolhas se conectariam na tela.")
    else:
        print("Veredito: FALHA. A conexão é fraca demais.")