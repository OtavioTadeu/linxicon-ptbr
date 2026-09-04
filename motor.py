from sentence_transformers import SentenceTransformer, util

# Fonte única de verdade para o limiar de conexão
THRESHOLD = 50.0

print("Carregando o modelo semântico (IA)...")
modelo = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Cache JIT: armazena vetores já calculados para evitar reprocessamento
_cache_vetores = {}

print("Carregando o dicionario em memoria...")
try:
    with open('dicionario_limpo.txt', 'r', encoding='utf-8') as arquivo:
        vocabulario_ptbr = set(linha.strip().lower() for linha in arquivo)
except FileNotFoundError:
    print("[ERRO] O arquivo 'dicionario_limpo.txt' nao foi encontrado.")
    print("Rode o script 'limpar.py' primeiro!")
    exit()

def _obter_vetor(palavra):
    if palavra not in _cache_vetores:
        _cache_vetores[palavra] = modelo.encode(palavra)
    return _cache_vetores[palavra]

def calcular_similaridade(palavra1, palavra2):
    vetor1 = _obter_vetor(palavra1)
    vetor2 = _obter_vetor(palavra2)
    return util.cos_sim(vetor1, vetor2).item() * 100

def eh_palavra_valida(palavra):
    return palavra in vocabulario_ptbr

def classificar_feedback(similaridade):
    """Retorna feedback textual baseado na proximidade ao threshold."""
    if similaridade >= THRESHOLD:
        return "conectou"
    elif similaridade >= THRESHOLD - 10:
        return "quente"
    elif similaridade >= THRESHOLD - 25:
        return "morno"
    else:
        return "frio"

def validar_conceitos(conceitos):
    """Verifica quais conceitos existem no dicionário. Retorna lista de ausentes."""
    ausentes = [p for p in conceitos if p not in vocabulario_ptbr]
    if ausentes:
        print(f"[AVISO] Conceitos ausentes no dicionario: {ausentes}")
    else:
        print("[OK] Todos os conceitos existem no dicionario.")
    return ausentes

if __name__ == "__main__":
    print("\n--- Validador Semântico Linxicon (PT-BR) ---")
    print("Sistemas carregados! Digite 'sair' para encerrar.")
    
    while True:
        p1 = input("\nPrimeira palavra: ").strip().lower()
        if p1 == 'sair':
            break
            
        if not eh_palavra_valida(p1):
            print(f"[X] Bloqueado: A palavra '{p1}' não foi encontrada no dicionário.")
            continue
            
        p2 = input("Segunda palavra: ").strip().lower()
        if p2 == 'sair':
            break
            
        if not eh_palavra_valida(p2):
            print(f"[X] Bloqueado: A palavra '{p2}' não foi encontrada no dicionário.")
            continue
        porcentagem = calcular_similaridade(p1, p2)
        
        print(f"Similaridade entre '{p1}' e '{p2}': {porcentagem:.1f}%")
        
        if porcentagem >= THRESHOLD:
            print("Veredito: SUCESSO! (As bolhas se conectariam)")
        else:
            print("Veredito: FALHA. (A conexão é muito fraca)")