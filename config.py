ARQUIVO_MAPA = "kanto.txt"

LINHAS = 42
COLUNAS = 150

SIMBOLO_ORIGEM = "1"
SIMBOLO_DESTINO = "U"

CUSTO_TERRENO = {
    "M": 200,  # Montanha
    "A": 30,   # Água
    "F": 15,   # Floresta
    "R": 5,    # Rochoso
    ".": 1,    # Livre
}

CUSTO_ORIGEM_DESTINO = 1
# A célula inicial também entra no custo da rota (+1), como a final.

CONTAR_CELULA_INICIAL = True
CUSTO_GINASIO = 0

DIFICULDADE = {
    "2": 35, 
    "3": 40, 
    "4": 45, 
    "5": 50, 
    "6": 55, 
    "7": 60, 
    "8": 65, 
    "9": 70, 
    "B": 75, 
    "C": 80, 
    "D": 85, 
    "E": 90, 
    "G": 95, 
    "H": 100,
    "I": 110,
    "J": 120,
    "K": 130,
    "L": 140,
    "N": 150,
    "O": 155,
    "P": 160,
    "Q": 165,
    "S": 170,
    "T": 180,
}

PODER = {
    "Pikachu": 1.5,
    "Bulbassauro": 1.4,
    "Rattata": 1.3,
    "Caterpie": 1.2,
    "Weedle": 1.1,
}

ENERGIA_INICIAL = 6
MIN_POKEMONS_VIVOS = 1

# Busca local das batalhas (Etapa 5)
SA_TEMPERATURA_INICIAL = 10.0
SA_TEMPERATURA_FINAL = 0.001
SA_ITERACOES = 50000
HC_REINICIOS = 20
