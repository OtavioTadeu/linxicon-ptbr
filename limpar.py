arquivo_entrada = "br-utf8.txt" 
arquivo_saida = "dicionario_limpo.txt"

ARTIGOS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "ao", "aos", "à", "às", "do", "da", "dos", "das",
    "no", "na", "nos", "nas", "num", "numa", "nuns", "numas",
    "dum", "duma", "duns", "dumas",
}

PRONOMES = {
    "eu", "tu", "ele", "ela", "nós", "nos", "vós", "vos", "eles", "elas",
    "me", "te", "se", "lhe", "lhes", "mim", "ti", "si",
    "comigo", "contigo", "consigo", "conosco", "convosco",
    "meu", "minha", "meus", "minhas", "teu", "tua", "teus", "tuas",
    "seu", "sua", "seus", "suas", "nosso", "nossa", "nossos", "nossas",
    "vosso", "vossa", "vossos", "vossas",
    "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "aqueles", "aquelas", "isto", "isso", "aquilo",
    "algum", "alguma", "alguns", "algumas", "nenhum", "nenhuma", "nenhuns", "nenhumas",
    "todo", "toda", "todos", "todas", "outro", "outra", "outros", "outras",
    "muito", "muita", "muitos", "muitas", "pouco", "pouca", "poucos", "poucas",
    "vários", "várias", "qualquer", "quaisquer", "certo", "certa", "certos", "certas",
    "tanto", "tanta", "tantos", "tantas",
    "que", "quem", "qual", "quais", "quanto", "quanta", "quantos", "quantas",
    "cujo", "cuja", "cujos", "cujas", "onde",
}

CONJUNCOES = {
    "e", "nem", "mas", "porém", "todavia", "contudo",
    "ou", "ora", "logo", "portanto",
    "que", "se", "porque", "porquanto",
    "como", "quando", "enquanto", "conquanto", "embora", "caso",
    "conforme", "segundo", "assim", "desde", "antes", "depois",
    "até", "para", "sem", "senão",
}

PALAVRAS_EXCLUIDAS = ARTIGOS | PRONOMES | CONJUNCOES
lista_negra = {"merda", "caralho", "porra", "cacete"}

palavras_limpas = set()
palavras_removidas = 0

print("Analisando o arquivo bruto e limpando os dados...")

with open(arquivo_entrada, "r", encoding="utf-8") as f:
    for linha in f:
        palavra_bruta = linha.strip()
        
        if not palavra_bruta:
            continue
            
        if palavra_bruta[0].isupper():
            palavras_removidas += 1
            continue
            
        palavra = palavra_bruta.lower()
        
        tamanho_valido = 2 <= len(palavra) <= 15
        sem_hifen = "-" not in palavra
        sem_espaco = " " not in palavra
        nao_e_palavrao = palavra not in lista_negra
        nao_e_stopword = palavra not in PALAVRAS_EXCLUIDAS
        
        if tamanho_valido and sem_hifen and sem_espaco and nao_e_palavrao and nao_e_stopword:
            palavras_limpas.add(palavra)
        else:
            palavras_removidas += 1

lista_final = sorted(list(palavras_limpas))

with open(arquivo_saida, "w", encoding="utf-8") as f:
    for p in lista_final:
        f.write(p + "\n")

print(f"✅ Arquivo gerado: {arquivo_saida}")
print(f"🔹 Total de palavras prontas para o jogo: {len(lista_final)}")
print(f"🔸 Palavras barradas pelo algoritmo: {palavras_removidas}")