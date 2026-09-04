from sentence_transformers import SentenceTransformer, util

print("Carregando o modelo semântico (IA)...")
modelo = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

print("Carregando o dicionário em memória...")
try:
    with open('dicionario_limpo.txt', 'r', encoding='utf-8') as arquivo:
        vocabulario_ptbr = set(linha.strip().lower() for linha in arquivo)
except FileNotFoundError:
    print("❌ Erro: O arquivo 'dicionario.txt' não foi encontrado.")
    print("Rode o script 'baixar_dicionario.py' primeiro!")
    exit()

def calcular_similaridade(palavra1, palavra2):
    vetor1 = modelo.encode(palavra1)
    vetor2 = modelo.encode(palavra2)
    return util.cos_sim(vetor1, vetor2).item() * 100

def eh_palavra_valida(palavra):
    return palavra in vocabulario_ptbr

if __name__ == "__main__":
    print("\n--- Validador Semântico Linxicon (PT-BR) ---")
    print("Sistemas carregados! Digite 'sair' para encerrar.")
    
    while True:
        p1 = input("\nPrimeira palavra: ").strip().lower()
        if p1 == 'sair':
            break
            
        if not eh_palavra_valida(p1):
            print(f"❌ Bloqueado: A palavra '{p1}' não foi encontrada no dicionário.")
            continue
            
        p2 = input("Segunda palavra: ").strip().lower()
        if p2 == 'sair':
            break
            
        if not eh_palavra_valida(p2):
            print(f"❌ Bloqueado: A palavra '{p2}' não foi encontrada no dicionário.")
            continue
        porcentagem = calcular_similaridade(p1, p2)
        
        print(f"✅ Similaridade entre '{p1}' e '{p2}': {porcentagem:.1f}%")
        
        if porcentagem >= 40.0:
            print("Veredito: SUCESSO! (As bolhas se conectariam)")
        else:
            print("Veredito: FALHA. (A conexão é muito fraca)")