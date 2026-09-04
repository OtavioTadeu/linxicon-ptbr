import random
from datetime import date
from sentence_transformers import util
import motor

CONCEITOS_BASE = [
    # Elementos e natureza
    "fogo", "água", "terra", "ar", "chuva", "vento", "trovão", "neve",
    "gelo", "tempestade", "vulcão", "fumaça", "lama", "poeira", "cinza",

    # Cosmos e geografia
    "sol", "lua", "estrela", "planeta", "céu", "horizonte", "abismo",
    "oceano", "deserto", "montanha", "vale", "ilha", "rio", "caverna",
    "floresta", "campo", "jardim", "pântano", "praia",

    # Flora e fauna
    "animal", "planta", "flor", "raiz", "semente", "árvore", "fruta",
    "pássaro", "peixe", "lobo", "serpente", "cavalo", "inseto", "fera",

    # Corpo humano
    "corpo", "sangue", "osso", "coração", "olho", "mão", "pele",
    "cérebro", "músculo", "nervo", "fôlego", "lágrima", "suor",

    # Pessoas e ciclo da vida
    "homem", "mulher", "criança", "velho", "humano", "bebê", "guerreiro",
    "sábio", "estranho", "herói", "fantasma", "gigante", "anão",

    # Emoções e sentimentos
    "amor", "ódio", "medo", "alegria", "tristeza", "raiva", "esperança",
    "saudade", "orgulho", "vergonha", "culpa", "coragem", "paixão",
    "solidão", "prazer", "angústia", "inveja", "gratidão",

    # Mente e conhecimento
    "mente", "alma", "sonho", "memória", "pensamento", "sabedoria",
    "loucura", "consciência", "instinto", "imaginação", "razão",

    # Tempo e existência
    "tempo", "espaço", "vida", "morte", "passado", "futuro", "eternidade",
    "momento", "início", "fim", "destino", "acaso", "ciclo",

    # Sociedade e poder
    "rei", "escravo", "povo", "família", "lei", "justiça", "liberdade",
    "poder", "riqueza", "pobreza", "revolução", "trono", "exílio",

    # Conflito e paz
    "paz", "guerra", "batalha", "vitória", "derrota", "conquista",
    "vingança", "perdão", "traição", "aliança", "cerco", "fuga",

    # Verdade e ilusão
    "verdade", "mentira", "segredo", "mistério", "realidade",
    "ilusão", "profecia", "enigma", "promessa", "silêncio",

    # Luz, sombra e clima
    "luz", "sombra", "escuridão", "aurora", "crepúsculo",
    "dia", "noite", "frio", "calor", "bruma",

    # Objetos e construções
    "espada", "escudo", "coroa", "chave", "porta", "ponte", "torre",
    "barco", "muro", "altar", "tumba", "bandeira", "corrente", "armadilha",

    # Matéria e ofícios
    "ferro", "ouro", "prata", "madeira", "vidro", "pedra", "cristal",
    "tecido", "corda", "tinta", "veneno", "remédio",

    # Arte, cultura e espiritualidade
    "música", "dança", "pintura", "teatro", "livro", "palavra", "canção",
    "ritual", "magia", "ciência", "tecnologia", "deus", "templo", "oração",

    # Alimento e sustento
    "pão", "vinho", "mel", "carne", "sal", "trigo", "colheita", "banquete",

    # Viagem e espaço
    "viagem", "casa", "caminho", "cidade", "navio", "mapa",
    "fronteira", "labirinto", "refúgio", "ruína",

    # Natureza abstrata
    "natureza", "caos", "ordem", "equilíbrio", "força",
    "fragilidade", "beleza", "perigo", "sorte", "sacrifício",

    # Som
    "som", "eco", "grito", "sussurro", "melodia", "ruído",
]

# Remove possíveis duplicatas mantendo a ordem
CONCEITOS_BASE = list(dict.fromkeys(CONCEITOS_BASE))

# #20: Validar conceitos contra o dicionário
motor.validar_conceitos(CONCEITOS_BASE)

print(f"Calculando IA para {len(CONCEITOS_BASE)} conceitos base (batch)...")
_vetores = motor.modelo.encode(CONCEITOS_BASE)
CACHE_VETORES = {p: v for p, v in zip(CONCEITOS_BASE, _vetores)}

# Cache do desafio diário (gera uma vez por dia)
_cache_diario = {"data": None, "caminho": None}

def buscar_proxima_palavra(palavra_atual, caminho_atual):
    vetor_atual = CACHE_VETORES[palavra_atual]
    opcoes = list(CONCEITOS_BASE)
    random.shuffle(opcoes)
    
    for candidata in opcoes:
        if candidata in caminho_atual:
            continue
            
        vetor_candidata = CACHE_VETORES[candidata]
        similaridade = util.cos_sim(vetor_atual, vetor_candidata).item() * 100

        if motor.THRESHOLD <= similaridade <= 75.0:
            return candidata, similaridade
            
    return None, 0

def _gerar_caminho_interno(qtd_saltos=3, tolerancia_inicial=15.0):
    """Gera um caminho sem seed — lógica pura do algoritmo."""

    tolerancia_maxima = motor.THRESHOLD - 1.0 
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
        return _gerar_caminho_interno(qtd_saltos, nova_tolerancia)
        
    print("Caminho ideal muito rígido. Reduzindo para 2 saltos complexos.")
    return _gerar_caminho_interno(qtd_saltos=2, tolerancia_inicial=20.0)

def gerar_desafio_diario(qtd_saltos=4):
    """Retorna o mesmo caminho durante o dia inteiro (seed por data)."""
    hoje = str(date.today())
    
    if _cache_diario["data"] == hoje:
        return _cache_diario["caminho"]
    
    random.seed(hash(hoje))
    caminho = _gerar_caminho_interno(qtd_saltos)
    random.seed()  # restaura aleatoriedade para modo prática
    
    _cache_diario["data"] = hoje
    _cache_diario["caminho"] = caminho
    return caminho

def gerar_pratica(qtd_saltos=4):
    """Gera um caminho aleatório para modo prática (sem seed fixa)."""
    return _gerar_caminho_interno(qtd_saltos)