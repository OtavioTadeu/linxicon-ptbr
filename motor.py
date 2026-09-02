from sentence_transformers import SentenceTransformer, util
from spellchecker import SpellChecker

# 1. Carrega o modelo semântico (Pesado)
print("Carregando o modelo semântico (IA)...")
modelo = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 2. Carrega o dicionário (Leve e rápido)
print("Carregando o dicionário de português...")
dicionario = SpellChecker(language='pt')

def calcular_similaridade(palavra1, palavra2):
    vetor1 = modelo.encode(palavra1)
    vetor2 = modelo.encode(palavra2)
    similaridade = util.cos_sim(vetor1, vetor2).item()
    return similaridade * 100

def eh_palavra_valida(palavra):
    # A função .known() verifica se a palavra existe na base de dados
    # Se retornar um conjunto vazio, a palavra não existe no idioma
    return len(dicionario.known([palavra])) > 0

if __name__ == "__main__":
    print("\n--- Validador Semântico Linxicon (PT-BR) ---")
    print("Sistemas carregados! Digite 'sair' para encerrar.")
    
    while True:
        p1 = input("\nPrimeira palavra: ").strip().lower()
        if p1 == 'sair':
            break
            
        # O Porteiro entra em ação aqui
        if not eh_palavra_valida(p1):
            print(f"❌ Bloqueado: A palavra '{p1}' não foi encontrada no dicionário.")
            continue
            
        p2 = input("Segunda palavra: ").strip().lower()
        if p2 == 'sair':
            break
            
        # Valida a segunda palavra também
        if not eh_palavra_valida(p2):
            print(f"❌ Bloqueado: A palavra '{p2}' não foi encontrada no dicionário.")
            continue
        
        # Se as duas passaram, fazemos o cálculo pesado
        porcentagem = calcular_similaridade(p1, p2)
        
        print(f"✅ Similaridade entre '{p1}' e '{p2}': {porcentagem:.1f}%")
        
        if porcentagem >= 40.0:
            print("Veredito: SUCESSO! (As bolhas se conectariam)")
        else:
            print("Veredito: FALHA. (A conexão é muito fraca)")