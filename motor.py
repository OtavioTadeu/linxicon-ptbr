from sentence_transformers import SentenceTransformer, util

print("Carregando o modelo (isso pode demorar na primeira execução)...")
modelo = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def calcular_similaridade(palavra1, palavra2):
    vetor1 = modelo.encode(palavra1)
    vetor2 = modelo.encode(palavra2)
    similaridade = util.cos_sim(vetor1, vetor2).item()
    return similaridade * 100

if __name__ == "__main__":
    print("\n--- Validador Semântico ---")
    print("O modelo foi carregado! Digite 'sair' para encerrar.")
    
    while True:
        p1 = input("\nPrimeira palavra: ").strip().lower()
        if p1 == 'sair':
            break
            
        p2 = input("Segunda palavra: ").strip().lower()
        if p2 == 'sair':
            break
        
        porcentagem = calcular_similaridade(p1, p2)
        
        print(f"Similaridade: {porcentagem:.1f}%")
        
        if porcentagem >= 40.0:
            print("Veredito: SUCESSO! (Conectou)")
        else:
            print("Veredito: FALHA. (Não conectou)")