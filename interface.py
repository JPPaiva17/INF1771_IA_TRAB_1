import argparse
import math
import os
import random
import unicodedata

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

import batalhas
import config
from astar_grid import astar
from distancias import carregar_distancias
from main import custo_inicial, expandidos_grid, simular
from mapa import Mapa
from rota import resolver_rota

LARGURA, ALTURA = 640, 400
FPS = 60
TAMANHO_CELULA = 4
MAPA_X, MAPA_Y = 20, 10
TELA_CIMA = pygame.Rect(20, 10, 600, 168)
TELA_BAIXO = pygame.Rect(20, 202, 600, 190)
PAINEIS_Y, PAINEIS_ALTURA = 218, 148
CONTROLES_Y = 370

ETAPA_PRONTO, ETAPA_ROTA, ETAPA_BATALHAS, ETAPA_JORNADA, ETAPA_RESULTADO = range(5)
NOMES_ETAPAS = [
    "PRONTO PARA COMEÇAR",
    "ETAPA 1/4 - ROTA (A* NOS ESTADOS)",
    "ETAPA 2/4 - BATALHAS (SIMULATED ANNEALING)",
    "ETAPA 3/4 - JORNADA (A* NO GRID)",
    "ETAPA 4/4 - RESULTADO",
]

VELOCIDADES = [0.25, 0.5, 1, 2, 4, 8, 16, 32]
VELOCIDADE_PADRAO = 3
ITERACOES_POR_PASSO_SA = 250
QUADROS_AGUA = 4
QUADROS_POR_ONDA = 20
LIMITE_CACHE_TEXTOS = 3000
LETRAS_POR_QUADRO = 1.5
QUADROS_PLACA = 150
QUADROS_ENTRADA_PLACA = 10
ZOOM_SA = 6.0

PESO_ROTA = 8
PESO_FIM_ROTA = 60
PESO_SA = 2
PESO_FIM_SA = 40
PESO_EXPANSAO = 0.15
PESO_CAMINHO = 20
PESO_PASSO_BASE = 1.5
DIVISOR_PESO_TERRENO = 40
PESO_BATALHA = 90
PESO_CHEGADA = 60

CORPO = (28, 28, 34)
CORPO_CLARO = (52, 52, 62)
BISEL = (10, 10, 14)
BISEL_BRILHO = (72, 72, 86)
LISTRA_ESCURA = (44, 50, 66)
LISTRA_CLARA = (52, 58, 76)
FAIXA = (36, 40, 52)
BRANCO = (248, 248, 248)
CREME = (255, 246, 214)
TINTA = (64, 64, 72)
SOMBRA_TINTA = (212, 212, 220)
TINTA_FRACA = (128, 128, 140)
SOMBRA_ESCURA = (16, 16, 22)
CONTORNO_CAIXA = (56, 56, 64)
FILETE = (184, 196, 216)
CINZA = (176, 176, 184)
CINZA_CLARO = (224, 224, 232)
AZUL = (64, 112, 200)
AZUL_CLARO = (200, 216, 248)
VERMELHO = (216, 64, 56)
LARANJA = (232, 128, 40)
AMARELO = (248, 200, 64)
VERDE = (64, 168, 88)
VERDE_ENERGIA = (88, 208, 104)
CIANO = (72, 176, 224)
ROSA = (232, 80, 120)

COR_EXPANDIDO = (248, 216, 96, 120)
COR_FRONTEIRA = (96, 200, 248, 170)
COR_CAMINHO = (240, 80, 96, 230)
COR_TRILHA = (248, 248, 248, 255)

CORES_POKEMON = [(248, 208, 64), (88, 184, 112), (176, 120, 200), (160, 216, 96), (232, 128, 80)]

CORES_TERRENO = {
    ".": {".": (152, 208, 120), "l": (120, 180, 96)},
    "F": {".": (40, 96, 56), "l": (88, 160, 88), "d": (56, 120, 64), "t": (104, 72, 48)},
    "M": {".": (176, 144, 112), "l": (208, 184, 152), "d": (136, 104, 80), "n": (248, 248, 240)},
    "R": {".": (216, 196, 152), "d": (176, 152, 112), "l": (236, 220, 184)},
    "A": {".": (88, 144, 216), "w": (152, 200, 244)},
}
PADROES_TERRENO = {
    ".": [["....", "....", "....", "...."], ["....", ".l.l", "....", "...."],
          ["....", "....", "l.l.", "...."], ["....", "....", "....", "...."]],
    "F": [[".ll.", "llll", "dlld", ".td."]],
    "M": [["..l.", ".lld", "lldd", "dddd"], ["..l.", ".lld", "lldd", "dddd"],
          ["..n.", ".nld", "lldd", "dddd"]],
    "R": [["....", ".d..", "...l", "...."], ["..l.", "....", "d...", "...d"]],
    "A": [["....", "ww..", "....", "..ww"]],
}

SPRITE_PREDIO = [
    ".RRRR.",
    "RrrrrR",
    "RRRRRR",
    "wwwwww",
    "wwddww",
    "wwddww",
]
SPRITE_BANDEIRA = [
    "kyyyy.",
    "kyyyyy",
    "kyyyy.",
    "k.....",
    "k.....",
    "kk....",
]
SPRITE_TREINADOR = [
    ".rrrr.",
    "rrrrrw",
    ".ssss.",
    "bbbbbb",
    "sbbbbs",
    ".k..k.",
]
CORES_GINASIO = {"R": (72, 88, 128), "r": (112, 136, 184), "w": (240, 232, 216), "d": TINTA}
CORES_GINASIO_VENCIDO = {"R": (184, 136, 40), "r": (240, 200, 80), "w": (240, 232, 216), "d": TINTA}
CORES_ORIGEM = {"R": (184, 56, 56), "r": (224, 96, 88), "w": (240, 232, 216), "d": TINTA}
CORES_BANDEIRA = {"k": TINTA, "y": AMARELO}
CORES_TREINADOR = {"r": (208, 64, 56), "w": BRANCO, "s": (248, 200, 160), "b": (56, 96, 168),
                   "k": (40, 40, 48)}

FONTE_5X7 = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 00100 01000",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    ";": "00000 01100 01100 00000 01100 00100 01000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    "+": "00000 00100 00100 11111 00100 00100 00000",
    "=": "00000 00000 11111 00000 11111 00000 00000",
    "/": "00000 00001 00010 00100 01000 10000 00000",
    "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000",
    ">": "01000 00100 00010 00001 00010 00100 01000",
    "<": "00010 00100 01000 10000 01000 00100 00010",
    "%": "11000 11001 00010 00100 01000 10011 00011",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "?": "01110 10001 00001 00010 00100 00000 00100",
    "'": "00100 00100 01000 00000 00000 00000 00000",
    "_": "00000 00000 00000 00000 00000 00000 11111",
    "*": "00000 00100 10101 01110 10101 00100 00000",
    "#": "01010 01010 11111 01010 11111 01010 01010",
    "[": "01110 01000 01000 01000 01000 01000 01110",
    "]": "01110 00010 00010 00010 00010 00010 01110",
    "|": "00100 00100 00100 00100 00100 00100 00100",
}

_cache_glifos = {}
_cache_textos = {}


# ---------------------------------------------------------------------------
# Texto em fonte de pixels (5x7, proporcional)
# ---------------------------------------------------------------------------
def normalizar(conteudo):
    """Tira os acentos e deixa em maiúsculas, que é o que a fonte sabe desenhar.

    Args:
        conteudo: texto qualquer.

    Returns:
        Texto em maiúsculas e sem acentos.
    """
    decomposto = unicodedata.normalize("NFKD", str(conteudo))
    sem_acentos = "".join(caractere for caractere in decomposto
                          if not unicodedata.combining(caractere))
    return sem_acentos.upper()


def _metricas(caractere):
    """Primeira coluna usada e largura de uma letra.

    Letras e símbolos são estreitados até as colunas acesas (fonte
    proporcional); os dígitos ficam todos com 5 colunas para os números
    ficarem alinhados.

    Args:
        caractere: letra já normalizada.

    Returns:
        Tupla (primeira_coluna, largura).
    """
    if caractere == " ":
        return 0, 3
    linhas = FONTE_5X7.get(caractere, FONTE_5X7["?"]).split()
    colunas_acesas = [coluna for coluna in range(5) if any(linha[coluna] == "1" for linha in linhas)]
    if caractere.isdigit() or not colunas_acesas:
        return 0, 5
    return colunas_acesas[0], colunas_acesas[-1] - colunas_acesas[0] + 1


def largura_texto(conteudo, escala=1):
    """Largura em pixels de um texto na fonte 5x7.

    Args:
        conteudo: texto.
        escala: tamanho de cada pixel da fonte.

    Returns:
        Largura em pixels.
    """
    normalizado = normalizar(conteudo)
    if not normalizado:
        return 0
    return (sum(_metricas(caractere)[1] + 1 for caractere in normalizado) - 1) * escala


def _glifo(caractere, cor, escala):
    """Superfície de uma letra da fonte (guardada em cache).

    Args:
        caractere: letra já normalizada.
        cor: cor RGB.
        escala: tamanho de cada pixel da fonte.

    Returns:
        pygame.Surface com a letra.
    """
    chave = (caractere, cor, escala)
    if chave not in _cache_glifos:
        primeira_coluna, largura = _metricas(caractere)
        linhas = FONTE_5X7.get(caractere, FONTE_5X7["?"]).split()
        superficie = pygame.Surface((largura * escala, 7 * escala), pygame.SRCALPHA)
        for y, linha in enumerate(linhas):
            for x in range(largura):
                if linha[primeira_coluna + x] == "1":
                    superficie.fill(cor, (x * escala, y * escala, escala, escala))
        _cache_glifos[chave] = superficie
    return _cache_glifos[chave]


def renderizar_texto(conteudo, cor, escala=1):
    """Superfície com um texto inteiro (guardada em cache).

    Args:
        conteudo: texto.
        cor: cor RGB.
        escala: tamanho de cada pixel da fonte.

    Returns:
        pygame.Surface com o texto.
    """
    chave = (conteudo, cor, escala)
    if chave not in _cache_textos:
        if len(_cache_textos) > LIMITE_CACHE_TEXTOS:
            _cache_textos.clear()
        normalizado = normalizar(conteudo)
        superficie = pygame.Surface((max(1, largura_texto(normalizado, escala)), 7 * escala),
                                    pygame.SRCALPHA)
        x = 0
        for caractere in normalizado:
            superficie.blit(_glifo(caractere, cor, escala), (x, 0))
            x += (_metricas(caractere)[1] + 1) * escala
        _cache_textos[chave] = superficie
    return _cache_textos[chave]


def texto(tela, conteudo, x, y, cor=TINTA, escala=1, sombra=SOMBRA_TINTA, alinhamento="esquerda"):
    """Escreve um texto com a fonte de pixels.

    O padrão é tinta escura com sombra clara, para as caixas brancas.

    Args:
        tela: superfície de destino.
        conteudo: texto.
        x: coordenada x (esquerda, centro ou direita, conforme alinhamento).
        y: coordenada y do topo.
        cor: cor RGB.
        escala: tamanho de cada pixel da fonte.
        sombra: cor da sombra (1 pixel abaixo e à direita) ou None.
        alinhamento: 'esquerda', 'centro' ou 'direita'.

    Returns:
        Largura do texto em pixels.
    """
    superficie = renderizar_texto(conteudo, cor, escala)
    if alinhamento == "direita":
        x -= superficie.get_width()
    elif alinhamento == "centro":
        x -= superficie.get_width() // 2
    if sombra is not None:
        tela.blit(renderizar_texto(conteudo, sombra, escala), (x + escala, y + escala))
    tela.blit(superficie, (x, y))
    return superficie.get_width()


def texto_claro(tela, conteudo, x, y, cor=BRANCO, **opcoes):
    """Texto claro com sombra escura, para fundos escuros.

    Args:
        tela: superfície de destino.
        conteudo: texto.
        x: coordenada x.
        y: coordenada y do topo.
        cor: cor RGB.
        **opcoes: escala e alinhamento, como em texto().

    Returns:
        Largura do texto em pixels.
    """
    return texto(tela, conteudo, x, y, cor, sombra=SOMBRA_ESCURA, **opcoes)


# ---------------------------------------------------------------------------
# Caixas, sprites e mapa
# ---------------------------------------------------------------------------
def escurecer(cor, fator=0.6):
    """Versão mais escura de uma cor.

    Args:
        cor: cor RGB.
        fator: multiplicador de cada componente.

    Returns:
        Cor RGB escurecida.
    """
    return tuple(int(componente * fator) for componente in cor)


def caixa(tela, retangulo, fundo=BRANCO, borda=CONTORNO_CAIXA, filete=FILETE, sombra=True):
    """Caixa branca de cantos arredondados, como as janelas de diálogo.

    Args:
        tela: superfície de destino.
        retangulo: pygame.Rect da caixa.
        fundo: cor de dentro.
        borda: cor do contorno.
        filete: cor da linha fina por dentro do contorno (ou None).
        sombra: se True, desenha uma sombra 2 pixels abaixo.
    """
    if sombra:
        pygame.draw.rect(tela, SOMBRA_ESCURA, retangulo.move(0, 2), border_radius=4)
    pygame.draw.rect(tela, borda, retangulo, border_radius=4)
    pygame.draw.rect(tela, fundo, retangulo.inflate(-4, -4), border_radius=3)
    if filete:
        pygame.draw.rect(tela, filete, retangulo.inflate(-6, -6), 1, border_radius=2)


def caixa_com_titulo(tela, retangulo, titulo, cor_titulo=AZUL):
    """Caixa branca com uma barra de título colorida no topo.

    Args:
        tela: superfície de destino.
        retangulo: pygame.Rect da caixa.
        titulo: texto da barra.
        cor_titulo: cor da barra.
    """
    caixa(tela, retangulo, filete=None)
    barra = pygame.Rect(retangulo.x + 3, retangulo.y + 3, retangulo.width - 6, 11)
    pygame.draw.rect(tela, cor_titulo, barra, border_radius=2)
    pygame.draw.line(tela, escurecer(cor_titulo, 0.75), barra.bottomleft, barra.bottomright)
    texto_claro(tela, titulo, barra.x + 4, barra.y + 2)


def pilula(tela, indice_pokemon, x, y, cores):
    """Etiqueta arredondada com a abreviação do pokémon na cor dele.

    Args:
        tela: superfície de destino.
        indice_pokemon: índice em batalhas.POKEMONS.
        x: x da esquerda.
        y: y do topo.
        cores: lista de cores dos pokémons.
    """
    cor = cores[indice_pokemon]
    retangulo = pygame.Rect(x, y, 22, 9)
    pygame.draw.rect(tela, escurecer(cor, 0.55), retangulo, border_radius=3)
    pygame.draw.rect(tela, cor, retangulo.inflate(-2, -2), border_radius=2)
    texto(tela, abreviacao(batalhas.POKEMONS[indice_pokemon]), retangulo.centerx, y + 1,
          escurecer(cor, 0.3), sombra=None, alinhamento="centro")


def barra_energia(tela, x, y, largura, energia):
    """Barra de energia no estilo barra de vida: verde, amarela e vermelha.

    Args:
        tela: superfície de destino.
        x: x da esquerda.
        y: y do topo.
        largura: largura total, contando a etiqueta 'EN'.
        energia: energia atual do pokémon.
    """
    fracao = max(0, energia) / config.ENERGIA_INICIAL
    if fracao > 0.5:
        cor = VERDE_ENERGIA
    elif fracao > 0.2:
        cor = AMARELO
    else:
        cor = VERMELHO
    pygame.draw.rect(tela, TINTA, (x, y, largura, 9), border_radius=3)
    texto(tela, "EN", x + 3, y + 1, AMARELO, sombra=None)
    interno = pygame.Rect(x + 15, y + 2, largura - 17, 5)
    pygame.draw.rect(tela, (88, 88, 96), interno)
    preenchido = int(round(interno.width * fracao))
    if preenchido:
        tela.fill(cor, (interno.x, interno.y, preenchido, interno.height))
        tela.fill(tuple(min(255, componente + 48) for componente in cor),
                  (interno.x, interno.y, preenchido, 2))


def criar_sprite(padrao, cores, contorno=SOMBRA_ESCURA):
    """Monta um sprite a partir de um desenho em texto, com contorno de 1 pixel.

    Args:
        padrao: lista de strings; '.' é transparente e cada outra letra é
            uma chave de cores.
        cores: dict letra -> cor RGB.
        contorno: cor do contorno.

    Returns:
        pygame.Surface 2 pixels maior que o desenho em cada direção.
    """
    altura, largura = len(padrao), len(padrao[0])
    superficie = pygame.Surface((largura + 2, altura + 2), pygame.SRCALPHA)
    for y, linha in enumerate(padrao):
        for x, simbolo in enumerate(linha):
            if simbolo != ".":
                superficie.fill(contorno, (x, y, 3, 3))
    for y, linha in enumerate(padrao):
        for x, simbolo in enumerate(linha):
            if simbolo != ".":
                superficie.set_at((x + 1, y + 1), cores[simbolo])
    return superficie


def criar_insignia(cor, letra):
    """Insígnia redonda 12x12 de um pokémon, com a inicial no meio.

    Args:
        cor: cor do pokémon.
        letra: inicial do nome.

    Returns:
        pygame.Surface 12x12.
    """
    superficie = pygame.Surface((12, 12), pygame.SRCALPHA)
    for y in range(12):
        for x in range(12):
            distancia_centro = math.hypot(x - 5.5, y - 5.5)
            if distancia_centro <= 5.8:
                superficie.set_at((x, y), escurecer(cor) if distancia_centro > 4.6 else cor)
    glifo = _glifo(normalizar(letra), escurecer(cor, 0.35), 1)
    superficie.blit(glifo, ((12 - glifo.get_width()) // 2, 3))
    return superficie


def criar_tile(terreno, variante, quadro_agua=0):
    """Tile 4x4 de um terreno.

    Args:
        terreno: símbolo do terreno ('.', 'R', 'F', 'A', 'M').
        variante: índice do desenho entre as variações do terreno.
        quadro_agua: deslocamento das ondas (só para a água).

    Returns:
        pygame.Surface 4x4.
    """
    padroes = PADROES_TERRENO[terreno]
    padrao = padroes[variante % len(padroes)]
    if terreno == "A":
        deslocamento = quadro_agua % TAMANHO_CELULA
        padrao = [linha[-deslocamento:] + linha[:-deslocamento] if deslocamento else linha
                  for linha in padrao]
    cores = CORES_TERRENO[terreno]
    tile = pygame.Surface((TAMANHO_CELULA, TAMANHO_CELULA))
    for y, linha in enumerate(padrao):
        for x, simbolo in enumerate(linha):
            tile.set_at((x, y), cores[simbolo])
    return tile


def variante_da_celula(linha, coluna):
    """Escolhe, de forma fixa, qual variação de tile usar numa célula.

    Args:
        linha: linha da célula.
        coluna: coluna da célula.

    Returns:
        Número inteiro (o tile usa o resto pela quantidade de variações).
    """
    return (linha * 7 + coluna * 13 + (linha * coluna) % 7) % 12


def criar_superficies_mapa(mapa):
    """Desenha o mapa inteiro uma vez por quadro da animação da água.

    Args:
        mapa: objeto Mapa.

    Returns:
        Lista com QUADROS_AGUA superfícies do mapa.
    """
    tiles = {}
    superficies = []
    for quadro_agua in range(QUADROS_AGUA):
        superficie = pygame.Surface((mapa.colunas * TAMANHO_CELULA, mapa.linhas * TAMANHO_CELULA))
        for linha, conteudo in enumerate(mapa.grid):
            for coluna, simbolo in enumerate(conteudo):
                terreno = simbolo if simbolo in config.CUSTO_TERRENO else "."
                variante = variante_da_celula(linha, coluna) % len(PADROES_TERRENO[terreno])
                chave = (terreno, variante, quadro_agua if terreno == "A" else 0)
                if chave not in tiles:
                    tiles[chave] = criar_tile(*chave)
                superficie.blit(tiles[chave], (coluna * TAMANHO_CELULA, linha * TAMANHO_CELULA))
        superficies.append(superficie)
    return superficies


def criar_console():
    """Desenha o corpo do console de duas telas (fixo, feito uma vez).

    Returns:
        pygame.Surface LARGURA x ALTURA.
    """
    console = pygame.Surface((LARGURA, ALTURA))
    console.fill(CORPO)
    for tela in (TELA_CIMA, TELA_BAIXO):
        moldura = tela.inflate(10, 10)
        pygame.draw.rect(console, BISEL_BRILHO, moldura.move(0, -1), border_radius=6)
        pygame.draw.rect(console, BISEL, moldura, border_radius=6)
        pygame.draw.rect(console, SOMBRA_ESCURA, tela.inflate(2, 2))

    dobradica = pygame.Rect(10, TELA_CIMA.bottom + 7, LARGURA - 20, 9)
    pygame.draw.rect(console, CORPO_CLARO, dobradica, border_radius=4)
    for x in (dobradica.x + 4, dobradica.right - 64):
        pygame.draw.rect(console, BISEL, (x, dobradica.y + 2, 60, 5), border_radius=2)
        pygame.draw.line(console, BISEL_BRILHO, (x + 2, dobradica.y + 3), (x + 57, dobradica.y + 3))
    pygame.draw.rect(console, (72, 200, 248), (LARGURA // 2 - 2, dobradica.y + 3, 4, 3))

    for y in range(TELA_BAIXO.height):
        for x in range(0, TELA_BAIXO.width, 1):
            cor = LISTRA_CLARA if (x + y) % 8 < 2 else LISTRA_ESCURA
            console.set_at((TELA_BAIXO.x + x, TELA_BAIXO.y + y), cor)
    return console


def centro_da_celula(celula):
    """Pixel central de uma célula do mapa na tela.

    Args:
        celula: (linha, coluna).

    Returns:
        Tupla (x, y).
    """
    linha, coluna = celula
    return (MAPA_X + coluna * TAMANHO_CELULA + TAMANHO_CELULA // 2,
            MAPA_Y + linha * TAMANHO_CELULA + TAMANHO_CELULA // 2)


def abreviacao(pokemon):
    """Três primeiras letras do nome, em maiúsculas.

    Args:
        pokemon: nome do pokémon.

    Returns:
        Abreviação, ex.: 'PIK'.
    """
    return normalizar(pokemon)[:3]


def lista_de_nomes(nomes):
    """Junta nomes no formato 'A, B E C'.

    Args:
        nomes: lista de nomes.

    Returns:
        Texto com os nomes.
    """
    if len(nomes) == 1:
        return nomes[0]
    return ", ".join(nomes[:-1]) + " E " + nomes[-1]


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
class Interface:
    """Janela que mostra o trabalho rodando, etapa por etapa.

    As etapas são produzidas por um gerador (_roteiro): cada `yield` é um
    passo da animação e devolve (peso, fim_de_etapa). O peso diz quantos
    quadros esse passo fica na tela na velocidade 1x; fim_de_etapa marca
    onde o botão ETAPA para.

    Attributes:
        ativa: False quando o usuário fecha a janela.
        rodando: True enquanto a animação avança sozinha.
        terminado: True depois do resultado final.
        etapa: etapa atual (ETAPA_PRONTO ... ETAPA_RESULTADO).
    """

    def __init__(self, semente=0):
        self.semente = semente
        self.mapa = Mapa()
        self.tabela_distancias = carregar_distancias(self.mapa)
        self.resultado_rota = resolver_rota(self.tabela_distancias)
        self.ordem = self.resultado_rota.ordem
        self.ginasios_na_ordem = self.resultado_rota.ginasios
        self.indice_do_ginasio = {ginasio: indice for indice, ginasio in enumerate(batalhas.GINASIOS)}
        self.expandidos_tabela = expandidos_grid(self.tabela_distancias,
                                                 list(self.tabela_distancias.pontos))

        self.console = criar_console()
        self.superficies_mapa = criar_superficies_mapa(self.mapa)
        self.tiles_legenda = {terreno: pygame.transform.scale(criar_tile(terreno, 0), (8, 8))
                              for terreno in config.CUSTO_TERRENO}
        self.sprite_ginasio = criar_sprite(SPRITE_PREDIO, CORES_GINASIO)
        self.sprite_ginasio_vencido = criar_sprite(SPRITE_PREDIO, CORES_GINASIO_VENCIDO)
        self.sprite_origem = criar_sprite(SPRITE_PREDIO, CORES_ORIGEM)
        self.sprite_destino = criar_sprite(SPRITE_BANDEIRA, CORES_BANDEIRA)
        self.sprite_treinador = criar_sprite(SPRITE_TREINADOR, CORES_TREINADOR)
        self.cores_pokemon = [CORES_POKEMON[indice % len(CORES_POKEMON)]
                              for indice in range(batalhas.TOTAL_POKEMONS)]
        self.insignias = [criar_insignia(cor, pokemon[0])
                          for cor, pokemon in zip(self.cores_pokemon, batalhas.POKEMONS)]
        self.clarao = pygame.Surface(TELA_CIMA.size, pygame.SRCALPHA)

        self.ativa = True
        self.mostrar_rotulos = True
        self.indice_velocidade = VELOCIDADE_PADRAO
        self.quadro = 0
        self.posicao_mouse = (0, 0)
        self.botoes = self._montar_botoes()
        self.reiniciar()

    def reiniciar(self):
        """Volta tudo para o começo (o resultado é o mesmo: a semente é fixa)."""
        tamanho_mapa = (self.mapa.colunas * TAMANHO_CELULA, self.mapa.linhas * TAMANHO_CELULA)
        self.etapa = ETAPA_PRONTO
        self.rodando = False
        self.terminado = False
        self.espera = 0.0
        self.roteiro = self._roteiro()

        self.placa = None
        self.dialogo = None
        self._falar(["BEM-VINDO A KANTO! 24 GINÁSIOS ESPERAM POR VOCÊ.",
                     "APERTE ESPAÇO PARA COMEÇAR A JORNADA."])

        self.segmentos_rota = 0
        self.custo_rota_planejado = None

        self.escala_exibida = None
        self.iteracao_sa = 0
        self.temperatura_sa = config.SA_TEMPERATURA_INICIAL
        self.custo_atual_sa = None
        self.melhor_custo_sa = None
        self.historico_iteracoes = []
        self.historico_atual = []
        self.historico_melhor = []
        self.historico_temperatura = []
        self.escala = None

        self.camada_busca = pygame.Surface(tamanho_mapa, pygame.SRCALPHA)
        self.camada_trilha = pygame.Surface(tamanho_mapa, pygame.SRCALPHA)
        self.indice_trecho = 0
        self.trecho = None
        self.buscando = False
        self.ultimo_expandido = None
        self.expandidos_trecho = 0
        self.expandidos_grid_jornada = 0
        self.passos_trecho = 0
        self.custo_trecho = None
        self.posicao_agente = self.mapa.origem
        self.andando = False
        self.energia = {pokemon: config.ENERGIA_INICIAL for pokemon in batalhas.POKEMONS}
        self.custo_rota_jornada = None
        self.custo_batalhas_jornada = None
        self.ginasios_vencidos = set()
        self.batalha = None

        self.resultado = None
        self.mostrar_resumo = False

    def _mostrar_placa(self, conteudo):
        """Placa que desliza no canto da tela de cima, como placa de local.

        Args:
            conteudo: texto da placa.
        """
        self.placa = (conteudo, self.quadro)

    def _falar(self, linhas, em_cima=False):
        """Abre a caixa de diálogo da tela de cima (texto aparece letra a letra).

        Args:
            linhas: lista de linhas de texto.
            em_cima: se True, a caixa fica no topo do mapa em vez de embaixo.
        """
        self.dialogo = {"linhas": linhas, "quadro": self.quadro, "em_cima": em_cima}

    # -----------------------------------------------------------------------
    # Roteiro (o que acontece em cada passo)
    # -----------------------------------------------------------------------
    def _roteiro(self):
        """Gerador com todas as etapas, na ordem.

        Yields:
            Tuplas (peso, fim_de_etapa).
        """
        yield from self._etapa_rota()
        yield from self._etapa_batalhas()
        yield from self._etapa_jornada()
        self._etapa_resultado()

    def _etapa_rota(self):
        """Mostra a ordem de visita encontrada pelo A* nos estados (posição, visitados).

        Yields:
            Um passo por trecho da rota desenhado.
        """
        self.etapa = ETAPA_ROTA
        self.dialogo = None
        self._mostrar_placa("ROTA - A* NOS ESTADOS")
        for segmentos in range(1, len(self.ordem)):
            self.segmentos_rota = segmentos
            yield PESO_ROTA, False
        self.custo_rota_planejado = custo_inicial() + self.resultado_rota.custo
        self._falar([f"O A* ACHOU A ORDEM ÓTIMA DOS 24 GINÁSIOS EXPANDINDO "
                     f"{self.resultado_rota.expandidos} ESTADOS.",
                     f"CUSTO DA ROTA: {self.custo_rota_planejado:.6f} MIN."])
        yield PESO_FIM_ROTA, True

    def _etapa_batalhas(self):
        """Roda o Simulated Annealing aos poucos para animar a busca.

        É a mesma lógica (e a mesma sequência de sorteios) de
        batalhas.simulated_annealing, só que pausando a cada
        ITERACOES_POR_PASSO_SA iterações para a tela acompanhar.

        Yields:
            Um passo a cada ITERACOES_POR_PASSO_SA iterações.
        """
        self.etapa = ETAPA_BATALHAS
        self.dialogo = None
        self._mostrar_placa("BATALHAS - SIMULATED ANNEALING")
        rng = random.Random(self.semente)
        escala = batalhas.escala_aleatoria(rng)
        usos_por_pokemon = batalhas.usos(escala)
        custo_atual = batalhas.custo(escala)
        melhor_custo, melhor_escala = custo_atual, escala[:]

        iteracoes = config.SA_ITERACOES
        fator_resfriamento = (config.SA_TEMPERATURA_FINAL
                              / config.SA_TEMPERATURA_INICIAL) ** (1 / iteracoes)
        temperatura = config.SA_TEMPERATURA_INICIAL
        self.escala_exibida = escala
        self._registrar_sa(0, temperatura, custo_atual, melhor_custo)

        for iteracao in range(iteracoes):
            movimento = batalhas.vizinho_aleatorio(escala, usos_por_pokemon, rng)
            variacao = batalhas.delta(escala, movimento[0])

            if variacao < 0 or rng.random() < math.exp(-variacao / temperatura):
                batalhas.aplicar(escala, usos_por_pokemon, movimento)
                custo_atual += variacao
                if custo_atual < melhor_custo - batalhas.TOLERANCIA:
                    melhor_custo, melhor_escala = custo_atual, escala[:]

            temperatura *= fator_resfriamento
            if (iteracao + 1) % ITERACOES_POR_PASSO_SA == 0 or iteracao == iteracoes - 1:
                self._registrar_sa(iteracao + 1, temperatura, custo_atual, melhor_custo)
                yield PESO_SA, False

        self.escala = melhor_escala
        self.escala_exibida = melhor_escala
        self.melhor_custo_sa = batalhas.custo(melhor_escala)
        yield PESO_FIM_SA, True

    def _registrar_sa(self, iteracao, temperatura, custo_atual, melhor_custo):
        """Guarda um ponto da busca para os painéis e os gráficos.

        Args:
            iteracao: iterações já feitas.
            temperatura: temperatura atual.
            custo_atual: custo da escala atual.
            melhor_custo: melhor custo até agora.
        """
        self.iteracao_sa = iteracao
        self.temperatura_sa = temperatura
        self.custo_atual_sa, self.melhor_custo_sa = custo_atual, melhor_custo
        self.historico_iteracoes.append(iteracao)
        self.historico_atual.append(custo_atual)
        self.historico_melhor.append(melhor_custo)
        self.historico_temperatura.append(temperatura)

    def _etapa_jornada(self):
        """Percorre a rota: em cada trecho roda o A* no grid e depois anda e batalha.

        Yields:
            Um passo por célula expandida, um ao mostrar o caminho, um por
            célula andada e um na batalha (ou na chegada ao destino).
        """
        self.etapa = ETAPA_JORNADA
        self.custo_rota_jornada = custo_inicial()
        self.custo_batalhas_jornada = 0.0
        pontos = self.tabela_distancias.pontos
        total_trechos = len(self.ordem) - 1

        for indice_trecho, (partida, chegada) in enumerate(zip(self.ordem, self.ordem[1:])):
            self.indice_trecho = indice_trecho
            self.trecho = (partida, chegada)
            self.batalha = None
            self.dialogo = None
            destino = "DESTINO U" if chegada == config.SIMBOLO_DESTINO else f"GINÁSIO {chegada}"
            self._mostrar_placa(f"TRECHO {indice_trecho + 1}/{total_trechos} - {destino}")
            self.camada_busca.fill((0, 0, 0, 0))
            self.expandidos_trecho = 0
            self.custo_trecho = None
            self.passos_trecho = 0
            self.buscando = True

            registro = {}
            custo_trecho, caminho, _ = astar(self.mapa, pontos[partida], pontos[chegada],
                                             registro=registro)
            for celula in registro["expandidos"]:
                self._pintar_celula(self.camada_busca, celula, COR_EXPANDIDO)
                self.ultimo_expandido = celula
                self.expandidos_trecho += 1
                self.expandidos_grid_jornada += 1
                yield PESO_EXPANSAO, False

            for celula in registro["fronteira"]:
                self._pintar_celula(self.camada_busca, celula, COR_FRONTEIRA)
            for celula in caminho:
                self._pintar_celula(self.camada_busca, celula, COR_CAMINHO)
            self.ultimo_expandido = None
            self.buscando = False
            self.custo_trecho = custo_trecho
            self.passos_trecho = len(caminho) - 1
            yield PESO_CAMINHO, True

            self.andando = True
            for celula in caminho[1:]:
                self.posicao_agente = celula
                self._pintar_celula(self.camada_trilha, celula, COR_TRILHA, tamanho=2)
                custo_celula = self.mapa.custo(*celula)
                self.custo_rota_jornada += custo_celula
                yield PESO_PASSO_BASE + custo_celula / DIVISOR_PESO_TERRENO, False
            self.andando = False

            em_cima = pontos[chegada][0] >= self.mapa.linhas // 2
            if chegada in self.indice_do_ginasio:
                ginasio = self.indice_do_ginasio[chegada]
                mascara = self.escala[ginasio]
                lutadores = batalhas.nomes(mascara)
                for pokemon in lutadores:
                    self.energia[pokemon] -= 1
                tempo_da_batalha = batalhas.tempo_batalha(ginasio, mascara)
                self.custo_batalhas_jornada += tempo_da_batalha
                self.ginasios_vencidos.add(chegada)
                self.batalha = {
                    "ginasio": chegada,
                    "mascara": mascara,
                    "dificuldade": config.DIFICULDADE[chegada],
                    "poder": batalhas.PODER_POR_MASCARA[mascara],
                    "tempo": tempo_da_batalha,
                    "quadro": self.quadro,
                }
                verbo = "ENTRA" if len(lutadores) == 1 else "ENTRAM"
                self._falar([
                    f"O LÍDER DO GINÁSIO {chegada} (DIFICULDADE {config.DIFICULDADE[chegada]}) "
                    f"QUER BATALHAR!",
                    f"{lista_de_nomes(lutadores)} {verbo} NA BATALHA!",
                    f"VITÓRIA EM {config.DIFICULDADE[chegada]} / {self.batalha['poder']:.1f} = "
                    f"{tempo_da_batalha:.6f} MIN.",
                ], em_cima)
                yield PESO_BATALHA, True
            else:
                self._falar([
                    "VOCÊ CHEGOU AO DESTINO COM OS 24 GINÁSIOS VENCIDOS!",
                    f"C_TOTAL = {self.custo_rota_jornada + self.custo_batalhas_jornada:.6f} MIN.",
                ], em_cima)
                yield PESO_CHEGADA, True

    def _etapa_resultado(self):
        """Confere a jornada com main.simular e abre o resumo final.

        Raises:
            RuntimeError: se o que foi animado não bater com main.simular.
        """
        _, custo_rota, custo_batalhas, energia = simular(
            self.ordem, self.escala, self.tabela_distancias)
        if (custo_rota != self.custo_rota_jornada
                or abs(custo_batalhas - self.custo_batalhas_jornada) > 1e-9
                or energia != self.energia):
            raise RuntimeError("a jornada animada não bate com main.simular")
        self.resultado = {
            "custo_rota": custo_rota,
            "custo_batalhas": custo_batalhas,
            "custo_total": custo_rota + custo_batalhas,
            "energia": energia,
        }
        self.etapa = ETAPA_RESULTADO
        self.dialogo = None
        self.mostrar_resumo = True

    def _pintar_celula(self, camada, celula, cor, tamanho=TAMANHO_CELULA):
        """Pinta uma célula numa camada transparente do mapa.

        Args:
            camada: superfície do tamanho do mapa.
            celula: (linha, coluna).
            cor: cor RGBA.
            tamanho: lado do quadrado pintado, centralizado na célula.
        """
        linha, coluna = celula
        margem = (TAMANHO_CELULA - tamanho) // 2
        camada.fill(cor, (coluna * TAMANHO_CELULA + margem, linha * TAMANHO_CELULA + margem,
                          tamanho, tamanho))

    # -----------------------------------------------------------------------
    # Controles
    # -----------------------------------------------------------------------
    def _proximo_evento(self):
        """Avança o roteiro um passo.

        Returns:
            Tupla (peso, fim_de_etapa). No fim do roteiro, (0, True).
        """
        try:
            return next(self.roteiro)
        except StopIteration:
            self.terminado = True
            self.rodando = False
            return 0, True

    def alternar(self):
        """INICIAR / PAUSAR / CONTINUAR."""
        if not self.terminado:
            self.rodando = not self.rodando

    def passo(self):
        """Avança um único passo visível e pausa."""
        self.rodando = False
        while not self.terminado:
            peso, fim_de_etapa = self._proximo_evento()
            if peso > 0 or fim_de_etapa:
                break

    def proxima_etapa(self):
        """Avança até o próximo fim de etapa e pausa."""
        self.rodando = False
        while not self.terminado:
            _, fim_de_etapa = self._proximo_evento()
            if fim_de_etapa:
                break

    def mudar_velocidade(self, direcao):
        """Aumenta (+1) ou diminui (-1) a velocidade.

        Args:
            direcao: +1 ou -1.
        """
        self.indice_velocidade = max(0, min(len(VELOCIDADES) - 1, self.indice_velocidade + direcao))

    def alternar_resumo(self):
        """Mostra ou esconde o resumo final (só depois do fim)."""
        if self.etapa == ETAPA_RESULTADO:
            self.mostrar_resumo = not self.mostrar_resumo

    def _montar_botoes(self):
        """Posições dos botões da barra de controles.

        Returns:
            Lista de (ação, pygame.Rect).
        """
        larguras = [("alternar", 84), ("passo", 60), ("etapa", 70), ("mais_lento", 16),
                    ("velocidade", 48), ("mais_rapido", 16), ("reiniciar", 70), ("resumo", 60)]
        botoes = []
        x = TELA_BAIXO.x + 4
        for acao, largura in larguras:
            botoes.append((acao, pygame.Rect(x, CONTROLES_Y, largura, 18)))
            x += largura + 4
        return botoes

    def _rotulo_botao(self, acao):
        """Texto, tecla e se o botão está habilitado.

        Args:
            acao: nome da ação do botão.

        Returns:
            Tupla (texto, tecla, habilitado).
        """
        if acao == "alternar":
            if self.terminado:
                return "FIM", "", False
            if self.rodando:
                return "PAUSAR", "ESP", True
            return ("INICIAR" if self.etapa == ETAPA_PRONTO else "CONTINUAR"), "ESP", True
        if acao == "passo":
            return "PASSO", ">", not self.terminado
        if acao == "etapa":
            return "ETAPA", "ENTER", not self.terminado
        if acao == "mais_lento":
            return "-", "", self.indice_velocidade > 0
        if acao == "mais_rapido":
            return "+", "", self.indice_velocidade < len(VELOCIDADES) - 1
        if acao == "velocidade":
            return f"VEL {VELOCIDADES[self.indice_velocidade]:g}X", "", False
        if acao == "reiniciar":
            return "REINICIAR", "R", True
        return "RESUMO", "M", self.etapa == ETAPA_RESULTADO

    def executar_acao(self, acao):
        """Executa a ação de um botão.

        Args:
            acao: nome da ação.
        """
        acoes = {
            "alternar": self.alternar,
            "passo": self.passo,
            "etapa": self.proxima_etapa,
            "mais_lento": lambda: self.mudar_velocidade(-1),
            "mais_rapido": lambda: self.mudar_velocidade(+1),
            "reiniciar": self.reiniciar,
            "resumo": self.alternar_resumo,
        }
        if acao in acoes:
            acoes[acao]()

    def tratar_evento(self, evento):
        """Teclado, mouse e fechamento da janela.

        Args:
            evento: pygame.event.Event.
        """
        if evento.type == pygame.QUIT:
            self.ativa = False
        elif evento.type == pygame.MOUSEMOTION:
            self.posicao_mouse = evento.pos
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for acao, retangulo in self.botoes:
                if retangulo.collidepoint(evento.pos) and self._rotulo_botao(acao)[2]:
                    self.executar_acao(acao)
        elif evento.type == pygame.KEYDOWN:
            teclas = {
                pygame.K_SPACE: "alternar",
                pygame.K_RIGHT: "passo",
                pygame.K_RETURN: "etapa",
                pygame.K_KP_ENTER: "etapa",
                pygame.K_DOWN: "etapa",
                pygame.K_MINUS: "mais_lento",
                pygame.K_KP_MINUS: "mais_lento",
                pygame.K_PLUS: "mais_rapido",
                pygame.K_EQUALS: "mais_rapido",
                pygame.K_KP_PLUS: "mais_rapido",
                pygame.K_r: "reiniciar",
                pygame.K_m: "resumo",
            }
            if evento.key == pygame.K_ESCAPE:
                self.ativa = False
            elif evento.key == pygame.K_l:
                self.mostrar_rotulos = not self.mostrar_rotulos
            elif evento.key == pygame.K_f:
                pygame.display.toggle_fullscreen()
            elif evento.key in teclas:
                self.executar_acao(teclas[evento.key])

    def atualizar(self):
        """Avança a animação de acordo com a velocidade (chamado a cada quadro)."""
        self.quadro += 1
        if not self.rodando:
            return
        self.espera -= VELOCIDADES[self.indice_velocidade]
        while self.espera <= 0 and not self.terminado:
            peso, _ = self._proximo_evento()
            self.espera += peso

    # -----------------------------------------------------------------------
    # Desenho: tela de cima
    # -----------------------------------------------------------------------
    def desenhar(self, tela):
        """Desenha as duas telas.

        Args:
            tela: superfície LARGURA x ALTURA.
        """
        tela.blit(self.console, (0, 0))
        tela.set_clip(TELA_CIMA)
        if self.etapa == ETAPA_BATALHAS:
            self._desenhar_graficos_sa(tela)
        elif self.etapa == ETAPA_RESULTADO and self.mostrar_resumo:
            self._desenhar_resumo(tela)
        else:
            self._desenhar_mapa(tela)
            self._desenhar_clarao(tela)
            self._desenhar_dialogo(tela)
        self._desenhar_placa(tela)
        tela.set_clip(None)

        self._desenhar_faixa_de_status(tela)
        self._desenhar_painel_equipe(tela)
        self._desenhar_painel_central(tela)
        self._desenhar_painel_custos(tela)
        self._desenhar_controles(tela)

    def _piscando(self, periodo=30):
        """True na primeira metade de cada período de quadros.

        Args:
            periodo: duração do ciclo em quadros.

        Returns:
            True ou False, alternando com o tempo.
        """
        return self.quadro % periodo < periodo // 2

    def _desenhar_mapa(self, tela):
        quadro_agua = (self.quadro // QUADROS_POR_ONDA) % QUADROS_AGUA
        tela.blit(self.superficies_mapa[quadro_agua], (MAPA_X, MAPA_Y))

        if self.etapa in (ETAPA_ROTA, ETAPA_BATALHAS):
            pontos = self.tabela_distancias.pontos
            trechos = list(zip(self.ordem[:self.segmentos_rota], self.ordem[1:self.segmentos_rota + 1]))
            for partida, chegada in trechos:
                inicio, fim = centro_da_celula(pontos[partida]), centro_da_celula(pontos[chegada])
                pygame.draw.line(tela, SOMBRA_ESCURA, (inicio[0], inicio[1] + 1), (fim[0], fim[1] + 1))
                pygame.draw.line(tela, BRANCO, inicio, fim)

        if self.etapa >= ETAPA_JORNADA:
            if self.etapa == ETAPA_JORNADA:
                tela.blit(self.camada_busca, (MAPA_X, MAPA_Y))
            tela.blit(self.camada_trilha, (MAPA_X, MAPA_Y))
            if self.ultimo_expandido is not None:
                linha, coluna = self.ultimo_expandido
                tela.fill(BRANCO, (MAPA_X + coluna * TAMANHO_CELULA, MAPA_Y + linha * TAMANHO_CELULA,
                                   TAMANHO_CELULA, TAMANHO_CELULA))

        self._desenhar_pontos(tela)
        self._desenhar_treinador(tela)

    def _desenhar_pontos(self, tela):
        alvo = self.trecho[1] if self.etapa == ETAPA_JORNADA and self.trecho else None
        for simbolo, celula in self.tabela_distancias.pontos.items():
            x, y = centro_da_celula(celula)
            if simbolo == config.SIMBOLO_ORIGEM:
                sprite = self.sprite_origem
            elif simbolo == config.SIMBOLO_DESTINO:
                sprite = self.sprite_destino
            elif simbolo in self.ginasios_vencidos:
                sprite = self.sprite_ginasio_vencido
            else:
                sprite = self.sprite_ginasio
            tela.blit(sprite, (x - 4, y - 4))

            if simbolo == alvo and self._piscando(20):
                pygame.draw.rect(tela, BRANCO, (x - 6, y - 6, 12, 12), 1, border_radius=2)

            if self.batalha and self.batalha["ginasio"] == simbolo:
                quadros = self.quadro - self.batalha["quadro"]
                if quadros < 40:
                    raio = 4 + quadros // 3
                    cor = AMARELO if (quadros // 4) % 2 else BRANCO
                    pygame.draw.rect(tela, cor, (x - raio, y - raio, 2 * raio, 2 * raio), 1,
                                     border_radius=3)

            if self.mostrar_rotulos:
                linha, _ = celula
                rotulo_y = y - 15 if linha > 2 else y + 6
                largura = largura_texto(simbolo)
                pygame.draw.rect(tela, FAIXA, (x - largura // 2 - 2, rotulo_y - 1, largura + 4, 9),
                                 border_radius=2)
                cor = AMARELO if simbolo in self.ginasios_vencidos else BRANCO
                texto(tela, simbolo, x, rotulo_y, cor, sombra=None, alinhamento="centro")

    def _desenhar_treinador(self, tela):
        x, y = centro_da_celula(self.posicao_agente)
        pulo = 1 if self.andando and (self.quadro // 6) % 2 else 0
        tela.blit(self.sprite_treinador, (x - 4, y - 7 - pulo))

    def _desenhar_clarao(self, tela):
        """Pisca a tela de cima no começo de cada batalha."""
        if not self.batalha:
            return
        quadros = self.quadro - self.batalha["quadro"]
        if quadros < 14 and (quadros // 3) % 2 == 0:
            self.clarao.fill((255, 255, 255, 170))
            tela.blit(self.clarao, TELA_CIMA.topleft)

    def _desenhar_dialogo(self, tela):
        """Caixa de diálogo com o texto aparecendo letra a letra."""
        if not self.dialogo:
            return
        linhas = self.dialogo["linhas"]
        altura = 12 + 11 * len(linhas)
        y = TELA_CIMA.y + 4 if self.dialogo["em_cima"] else TELA_CIMA.bottom - altura - 4
        retangulo = pygame.Rect(TELA_CIMA.x + 4, y, TELA_CIMA.width - 8, altura)
        caixa(tela, retangulo)

        letras = int((self.quadro - self.dialogo["quadro"]) * LETRAS_POR_QUADRO)
        for indice, linha in enumerate(linhas):
            visivel = linha[:max(0, letras)]
            if visivel:
                texto(tela, visivel, retangulo.x + 10, retangulo.y + 7 + indice * 11)
            letras -= len(linha)
        if letras > 0 and self._piscando(30):
            seta_x, seta_y = retangulo.right - 14, retangulo.bottom - 10
            pygame.draw.polygon(tela, VERMELHO, [(seta_x, seta_y), (seta_x + 6, seta_y),
                                                 (seta_x + 3, seta_y + 3)])

    def _desenhar_placa(self, tela):
        """Placa de local que desliza para dentro e para fora no canto da tela."""
        if not self.placa:
            return
        conteudo, inicio = self.placa
        quadros = self.quadro - inicio
        if quadros > QUADROS_PLACA:
            return
        largura = largura_texto(conteudo) + 20
        entrada = min(quadros, QUADROS_PLACA - quadros, QUADROS_ENTRADA_PLACA) / QUADROS_ENTRADA_PLACA
        x = TELA_CIMA.x - largura + int((largura + 6) * entrada)
        retangulo = pygame.Rect(x, TELA_CIMA.y + 6, largura, 17)
        pygame.draw.rect(tela, SOMBRA_ESCURA, retangulo.move(0, 2), border_radius=3)
        pygame.draw.rect(tela, FAIXA, retangulo, border_radius=3)
        pygame.draw.rect(tela, BISEL_BRILHO, retangulo, 1, border_radius=3)
        pygame.draw.line(tela, VERMELHO, (retangulo.x + 4, retangulo.bottom - 3),
                         (retangulo.right - 5, retangulo.bottom - 3))
        texto_claro(tela, conteudo, retangulo.x + 10, retangulo.y + 4)

    def _desenhar_graficos_sa(self, tela):
        """Tela de cima durante o Simulated Annealing: curva de custo e zoom no mínimo."""
        retangulo = TELA_CIMA.inflate(-4, -4)
        caixa(tela, retangulo, sombra=False)
        x, y = retangulo.x + 10, retangulo.y + 26
        texto(tela, "CUSTO X ITERAÇÃO", x, y - 10, TINTA_FRACA)
        legenda_x = x + 110
        for rotulo, cor in (("ATUAL", CIANO), ("MELHOR", LARANJA), ("TEMPERATURA", CINZA)):
            tela.fill(cor, (legenda_x, y - 7, 8, 3))
            legenda_x += 12 + texto(tela, rotulo, legenda_x + 11, y - 10, TINTA_FRACA) + 8

        principal = pygame.Rect(x + 34, y, 330, 118)
        zoom = pygame.Rect(principal.right + 52, y, retangulo.right - principal.right - 62, 118)
        if len(self.historico_atual) < 2:
            return

        menor = min(self.historico_melhor)
        maior = max(self.historico_atual)
        self._desenhar_grafico(tela, principal, menor, maior, com_temperatura=True)
        texto(tela, f"{maior:.0f}", principal.x - 4, principal.y, TINTA_FRACA, alinhamento="direita")
        texto(tela, f"{menor:.0f}", principal.x - 4, principal.bottom - 7, TINTA_FRACA,
              alinhamento="direita")
        texto(tela, "0", principal.x, principal.bottom + 4, TINTA_FRACA)
        texto(tela, str(config.SA_ITERACOES), principal.right, principal.bottom + 4, TINTA_FRACA,
              alinhamento="direita")

        base = self.melhor_custo_sa
        texto(tela, f"ZOOM: MELHOR ATÉ +{ZOOM_SA:g}", zoom.x, y - 10, TINTA_FRACA)
        self._desenhar_grafico(tela, zoom, base, base + ZOOM_SA)
        texto(tela, f"+{ZOOM_SA:g}", zoom.x - 4, zoom.y, TINTA_FRACA, alinhamento="direita")
        texto(tela, "+0", zoom.x - 4, zoom.bottom - 7, TINTA_FRACA, alinhamento="direita")
        texto(tela, f"{base:.6f}", zoom.right, zoom.bottom + 4, LARANJA, alinhamento="direita")

    def _desenhar_grafico(self, tela, area, menor, maior, com_temperatura=False):
        """Linhas do custo atual e do melhor custo ao longo das iterações.

        Args:
            tela: superfície de destino.
            area: pygame.Rect do gráfico.
            menor: valor na base do gráfico.
            maior: valor no topo do gráfico.
            com_temperatura: se True, desenha também a temperatura (escala log).
        """
        pygame.draw.rect(tela, CINZA_CLARO, area)
        pygame.draw.rect(tela, CINZA, area, 1)
        for divisao in range(1, 4):
            linha_y = area.y + area.height * divisao // 4
            for linha_x in range(area.x + 2, area.right - 2, 4):
                tela.set_at((linha_x, linha_y), CINZA)
        amplitude = (maior - menor) or 1.0

        def ponto(iteracao, fracao):
            ponto_x = area.x + 1 + iteracao / config.SA_ITERACOES * (area.width - 3)
            ponto_y = area.bottom - 2 - fracao * (area.height - 4)
            return int(ponto_x), int(ponto_y)

        tela.set_clip(area.inflate(-2, -2).clip(TELA_CIMA))
        if com_temperatura:
            log_inicial = math.log(config.SA_TEMPERATURA_INICIAL)
            log_final = math.log(config.SA_TEMPERATURA_FINAL)
            pontos = [ponto(iteracao, (math.log(temperatura) - log_final) / (log_inicial - log_final))
                      for iteracao, temperatura in zip(self.historico_iteracoes,
                                                       self.historico_temperatura)]
            pygame.draw.lines(tela, CINZA, False, pontos)
        for historico, cor in ((self.historico_atual, CIANO), (self.historico_melhor, LARANJA)):
            pontos = [ponto(iteracao, (valor - menor) / amplitude)
                      for iteracao, valor in zip(self.historico_iteracoes, historico)]
            pygame.draw.lines(tela, cor, False, pontos)
        tela.set_clip(TELA_CIMA)

    def _desenhar_resumo(self, tela):
        """Tela de cima no fim: ordem de visita e pokémons de cada batalha."""
        retangulo = TELA_CIMA.inflate(-4, -4)
        caixa(tela, retangulo, sombra=False)
        x, y = retangulo.x + 10, retangulo.y + 6
        largura_rotulo = texto(tela, "ORDEM DE VISITA:", x, y, TINTA_FRACA)
        texto(tela, " > ".join(self.ordem), x + largura_rotulo + 6, y, AZUL)

        texto(tela, "POKÉMONS EM CADA BATALHA (NA ORDEM DE VISITA) E TEMPO EM MINUTOS", x, y + 13,
              TINTA_FRACA)
        metade = (len(self.ginasios_na_ordem) + 1) // 2
        largura_coluna = (retangulo.width - 20) // 2
        for numero, ginasio in enumerate(self.ginasios_na_ordem):
            coluna, linha = divmod(numero, metade)
            linha_x, linha_y = x + coluna * (largura_coluna + 6), y + 25 + linha * 11
            if linha % 2 == 0:
                tela.fill(CINZA_CLARO, (linha_x - 3, linha_y - 2, largura_coluna, 11))
            indice = self.indice_do_ginasio[ginasio]
            mascara = self.escala[indice]
            texto(tela, f"{numero + 1:02}", linha_x, linha_y, TINTA_FRACA)
            texto(tela, ginasio, linha_x + 16, linha_y, AZUL)
            texto(tela, f"D{config.DIFICULDADE[ginasio]}", linha_x + 26, linha_y, TINTA_FRACA)
            for pokemon in range(batalhas.TOTAL_POKEMONS):
                if mascara >> pokemon & 1:
                    pilula(tela, pokemon, linha_x + 52 + pokemon * 24, linha_y - 1, self.cores_pokemon)
            texto(tela, f"{batalhas.tempo_batalha(indice, mascara):.6f}",
                  linha_x + largura_coluna - 8, linha_y, TINTA, alinhamento="direita")

    # -----------------------------------------------------------------------
    # Desenho: tela de baixo
    # -----------------------------------------------------------------------
    def _desenhar_faixa_de_status(self, tela):
        faixa = pygame.Rect(TELA_BAIXO.x, TELA_BAIXO.y, TELA_BAIXO.width, 13)
        pygame.draw.rect(tela, FAIXA, faixa)
        pygame.draw.line(tela, BISEL_BRILHO, faixa.bottomleft, faixa.bottomright)
        texto_claro(tela, NOMES_ETAPAS[self.etapa], faixa.x + 6, faixa.y + 3)
        if self.terminado:
            situacao, cor = "CONCLUÍDO", VERDE_ENERGIA
        elif self.rodando:
            situacao, cor = "RODANDO", VERDE_ENERGIA
        else:
            situacao, cor = "PAUSADO", LARANJA
        largura = texto_claro(tela, situacao, faixa.right - 6, faixa.y + 3, cor, alinhamento="direita")
        pygame.draw.circle(tela, cor, (faixa.right - 14 - largura, faixa.y + 6), 2)

    def _energia_exibida(self):
        """Energia de cada pokémon no painel da equipe.

        Na etapa das batalhas mostra quanto sobraria com a escala atual do
        Simulated Annealing; nas outras, a energia real naquele momento.

        Returns:
            Lista de energias na ordem de batalhas.POKEMONS.
        """
        if self.etapa == ETAPA_BATALHAS and self.escala_exibida is not None:
            return [config.ENERGIA_INICIAL - uso for uso in batalhas.usos(self.escala_exibida)]
        return [self.energia[pokemon] for pokemon in batalhas.POKEMONS]

    def _desenhar_painel_equipe(self, tela):
        lutando = batalhas.nomes(self.batalha["mascara"]) if self.batalha else []
        for indice, (pokemon, energia) in enumerate(zip(batalhas.POKEMONS, self._energia_exibida())):
            cartao = pygame.Rect(TELA_BAIXO.x + 2, PAINEIS_Y + indice * 30, 168, 28)
            if pokemon in lutando:
                borda = LARANJA if self._piscando(16) else CONTORNO_CAIXA
                caixa(tela, cartao, fundo=CREME, borda=borda, filete=None)
            else:
                caixa(tela, cartao, filete=None)
            x, y = cartao.x, cartao.y
            tela.blit(self.insignias[indice], (x + 5, y + 8))
            texto(tela, pokemon, x + 22, y + 5)
            if energia <= 0 and self.etapa >= ETAPA_JORNADA:
                texto(tela, "SEM ENERGIA", cartao.right - 7, y + 5, VERMELHO, alinhamento="direita")
            else:
                texto(tela, f"PODER {config.PODER[pokemon]:g}", cartao.right - 7, y + 5,
                      TINTA_FRACA, alinhamento="direita")
            barra_energia(tela, x + 22, y + 15, cartao.width - 50, energia)
            texto(tela, f"{energia}/{config.ENERGIA_INICIAL}", cartao.right - 7, y + 16,
                  VERMELHO if energia <= 0 else TINTA, alinhamento="direita")

    def _desenhar_ordem(self, tela, x, y, quantidade_destacada, indice_atual=None):
        """Desenha a ordem de visita em duas linhas de 13 pontos.

        Args:
            tela: superfície de destino.
            x: x do primeiro ponto.
            y: y da primeira linha.
            quantidade_destacada: quantos pontos (a partir do início) aparecem acesos.
            indice_atual: posição na ordem que pisca (opcional).
        """
        por_linha = (len(self.ordem) + 1) // 2
        for posicao, simbolo in enumerate(self.ordem):
            linha, coluna = divmod(posicao, por_linha)
            ponto_x, ponto_y = x + coluna * 18, y + linha * 11
            if posicao == indice_atual:
                cor = VERMELHO if self._piscando(20) else TINTA
            elif posicao < quantidade_destacada:
                cor = AZUL
            else:
                cor = CINZA
            texto(tela, simbolo, ponto_x + 3, ponto_y, cor, alinhamento="centro")
            if posicao < len(self.ordem) - 1 and coluna < por_linha - 1:
                texto(tela, ">", ponto_x + 12, ponto_y, CINZA, sombra=None)

    def _desenhar_painel_central(self, tela):
        retangulo = pygame.Rect(TELA_BAIXO.x + 174, PAINEIS_Y, 250, PAINEIS_ALTURA)
        x, y = retangulo.x + 8, retangulo.y
        if self.etapa == ETAPA_PRONTO:
            caixa_com_titulo(tela, retangulo, "LEGENDA E CONTROLES")
            self._desenhar_legenda(tela, x, y)
        elif self.etapa == ETAPA_ROTA:
            caixa_com_titulo(tela, retangulo, "ROTA: A* SOBRE OS ESTADOS")
            self._desenhar_detalhes_rota(tela, x, y)
        elif self.etapa == ETAPA_BATALHAS:
            caixa_com_titulo(tela, retangulo, "QUEM LUTA EM CADA GINÁSIO", VERMELHO)
            self._desenhar_detalhes_sa(tela, x, y)
        elif self.etapa == ETAPA_JORNADA:
            caixa_com_titulo(tela, retangulo, "JORNADA", VERDE)
            self._desenhar_detalhes_jornada(tela, x, y)
        else:
            caixa_com_titulo(tela, retangulo, "RESULTADO FINAL", LARANJA)
            self._desenhar_detalhes_resultado(tela, x, y)

    def _desenhar_legenda(self, tela, x, y):
        terrenos = [(".", "LIVRE"), ("R", "ROCHOSO"), ("F", "FLORESTA"), ("A", "ÁGUA"), ("M", "MONTANHA")]
        for indice, (terreno, nome) in enumerate(terrenos):
            linha_y = y + 17 + indice * 12
            pygame.draw.rect(tela, TINTA, (x - 1, linha_y - 1, 10, 10))
            tela.blit(self.tiles_legenda[terreno], (x, linha_y))
            texto(tela, nome, x + 14, linha_y + 1)
            texto(tela, f"{config.CUSTO_TERRENO[terreno]} MIN", x + 104, linha_y + 1, TINTA_FRACA,
                  alinhamento="direita")

        sprites = [(self.sprite_ginasio, "GINÁSIO"), (self.sprite_ginasio_vencido, "VENCIDO"),
                   (self.sprite_origem, "INÍCIO (1)"), (self.sprite_destino, "DESTINO (U)"),
                   (self.sprite_treinador, "TREINADOR")]
        for indice, (sprite, nome) in enumerate(sprites):
            linha_y = y + 17 + indice * 12
            tela.blit(sprite, (x + 126, linha_y))
            texto(tela, nome, x + 138, linha_y + 1)

        explicacoes = [
            ("ESPAÇO", "INICIA / PAUSA"),
            (">", "AVANÇA UM PASSO"),
            ("ENTER", "AVANÇA UMA ETAPA"),
            ("+ / -", "VELOCIDADE"),
            ("L / F", "NOMES / TELA CHEIA"),
        ]
        for indice, (tecla, descricao) in enumerate(explicacoes):
            linha_y = y + 82 + indice * 11
            texto(tela, tecla, x, linha_y, AZUL)
            texto(tela, descricao, x + 42, linha_y, TINTA_FRACA)
        texto(tela, f"SEMENTE {self.semente}", retangulo_direita(x), y + 126, CINZA,
              alinhamento="direita")

    def _desenhar_detalhes_rota(self, tela, x, y):
        direita = retangulo_direita(x)
        texto(tela, "ESTADO = (POSIÇÃO, GINÁSIOS VISITADOS)", x, y + 17, TINTA_FRACA)
        texto(tela, "HEURÍSTICA: HELD-KARP (ADMISSÍVEL)", x, y + 28, TINTA_FRACA)
        texto(tela, "ESTADOS EXPANDIDOS", x, y + 42)
        texto(tela, str(self.resultado_rota.expandidos), direita, y + 42, AZUL, alinhamento="direita")
        texto(tela, "ESTADOS GERADOS", x, y + 53)
        texto(tela, str(self.resultado_rota.gerados), direita, y + 53, AZUL, alinhamento="direita")
        texto(tela, "CUSTO DA ROTA (C_ROTA)", x, y + 64)
        if self.custo_rota_planejado is not None:
            texto(tela, f"{self.custo_rota_planejado:.6f}", direita, y + 64, VERMELHO,
                  alinhamento="direita")
        texto(tela, "ORDEM DE VISITA", x, y + 80, TINTA_FRACA)
        self._desenhar_ordem(tela, x, y + 91, self.segmentos_rota + 1)
        texto(tela, "A ORDEM NÃO DEPENDE DAS BATALHAS:", x, y + 117, CINZA)
        texto(tela, "C_TOTAL = C_ROTA + C_BATALHAS", x, y + 128, CINZA)

    def _desenhar_detalhes_sa(self, tela, x, y):
        direita = retangulo_direita(x)
        for coluna, ginasio in enumerate(self.ginasios_na_ordem):
            coluna_x = x + coluna * 9
            texto(tela, ginasio, coluna_x + 4, y + 17, TINTA_FRACA, sombra=None, alinhamento="centro")
            mascara = self.escala_exibida[self.indice_do_ginasio[ginasio]]
            for pokemon in range(batalhas.TOTAL_POKEMONS):
                celula = pygame.Rect(coluna_x, y + 26 + pokemon * 8, 8, 6)
                if mascara >> pokemon & 1:
                    tela.fill(escurecer(self.cores_pokemon[pokemon], 0.7), celula)
                    tela.fill(self.cores_pokemon[pokemon], celula.inflate(-2, -2))
                else:
                    pygame.draw.rect(tela, CINZA_CLARO, celula, 1)

        linhas = [
            ("ITERAÇÃO", f"{self.iteracao_sa}/{config.SA_ITERACOES}", TINTA),
            ("TEMPERATURA", f"{self.temperatura_sa:.6f}", TINTA_FRACA),
            ("CUSTO ATUAL", f"{self.custo_atual_sa:.6f}", CIANO),
            ("MELHOR CUSTO", f"{self.melhor_custo_sa:.6f}", LARANJA),
        ]
        for indice, (rotulo, valor, cor) in enumerate(linhas):
            linha_y = y + 70 + indice * 11
            texto(tela, rotulo, x, linha_y)
            texto(tela, valor, direita, linha_y, cor, alinhamento="direita")
        texto(tela, "PIORA ACEITA COM PROB. EXP(-DELTA/T)", x, y + 117, CINZA)
        texto(tela, "T ALTA: EXPLORA.  T BAIXA: SÓ ACEITA MELHORA.", x, y + 128, CINZA)

    def _desenhar_detalhes_jornada(self, tela, x, y):
        direita = retangulo_direita(x)
        total_trechos = len(self.ordem) - 1
        partida, chegada = self.trecho if self.trecho else ("-", "-")
        texto(tela, f"TRECHO {self.indice_trecho + 1:02}/{total_trechos}", x, y + 17)
        texto(tela, f"{partida} > {chegada}", direita, y + 17, AZUL, alinhamento="direita")

        if self.buscando:
            situacao, cor = "A* NO GRID: BUSCANDO...", CIANO
        elif self.andando:
            situacao, cor = "ANDANDO PELO CAMINHO ÓTIMO", TINTA
        elif self.batalha:
            situacao, cor = "BATALHA!", VERMELHO
        elif self.trecho and self.trecho[1] == config.SIMBOLO_DESTINO and not self.buscando:
            situacao, cor = "CHEGOU AO DESTINO!", VERDE
        else:
            situacao, cor = "CAMINHO ÓTIMO ENCONTRADO", ROSA
        texto(tela, situacao, x, y + 28, cor)
        texto(tela, "EXPANDIDOS NO TRECHO", x, y + 39, TINTA_FRACA)
        texto(tela, str(self.expandidos_trecho), direita, y + 39, CIANO, alinhamento="direita")
        if self.custo_trecho is not None:
            texto(tela, f"{self.passos_trecho} PASSOS, CUSTO {self.custo_trecho}", x, y + 50,
                  TINTA_FRACA)

        quadro_batalha = pygame.Rect(x - 2, y + 62, 238, 38)
        pygame.draw.rect(tela, CREME if self.batalha else CINZA_CLARO, quadro_batalha, border_radius=3)
        if self.batalha:
            batalha = self.batalha
            texto(tela, f"GINÁSIO {batalha['ginasio']}  (DIFICULDADE {batalha['dificuldade']})",
                  x + 3, y + 66, VERMELHO)
            texto(tela, "LUTAM:", x + 3, y + 77)
            for posicao, pokemon in enumerate(batalhas.nomes(batalha["mascara"])):
                pilula(tela, batalhas.POKEMONS.index(pokemon), x + 40 + posicao * 25, y + 76,
                       self.cores_pokemon)
            texto(tela, f"TEMPO = {batalha['dificuldade']} / {batalha['poder']:.1f}"
                        f" = {batalha['tempo']:.6f}", x + 3, y + 88)
        else:
            texto(tela, "NENHUMA BATALHA AGORA", quadro_batalha.centerx, y + 78, CINZA,
                  alinhamento="centro")

        texto(tela, "ORDEM DE VISITA", x, y + 106, TINTA_FRACA)
        self._desenhar_ordem(tela, x, y + 117, self.indice_trecho + 1, self.indice_trecho + 1)

    def _desenhar_detalhes_resultado(self, tela, x, y):
        direita = retangulo_direita(x)
        texto(tela, "ESTADOS EXPANDIDOS PELO A*", x, y + 17, TINTA_FRACA)
        expandidos = [
            ("ROTA (ESTADOS)", f"{self.resultado_rota.expandidos} ({self.resultado_rota.gerados} GERADOS)"),
            ("GRID: TRECHOS DA ROTA", str(self.expandidos_grid_jornada)),
            ("GRID: TABELA COMPLETA", str(self.expandidos_tabela)),
        ]
        for indice, (rotulo, valor) in enumerate(expandidos):
            linha_y = y + 28 + indice * 11
            texto(tela, rotulo, x, linha_y)
            texto(tela, valor, direita, linha_y, CIANO, alinhamento="direita")

        texto(tela, "CUSTO TOTAL", x, y + 68, TINTA_FRACA)
        texto(tela, f"{self.resultado['custo_total']:.6f} MIN", x, y + 79, VERMELHO, escala=2)
        texto(tela, "ORDEM E BATALHAS NA TELA DE CIMA.", x, y + 106, CINZA)
        texto(tela, "M: TABELA / MAPA     R: REINICIAR", x, y + 117, CINZA)

    def _desenhar_painel_custos(self, tela):
        retangulo = pygame.Rect(TELA_BAIXO.right - 172, PAINEIS_Y, 170, PAINEIS_ALTURA)
        caixa_com_titulo(tela, retangulo, "CUSTOS (MIN)", TINTA)
        x, direita, y = retangulo.x + 8, retangulo.right - 8, retangulo.y

        if self.etapa >= ETAPA_JORNADA:
            texto(tela, "ACUMULADO NA JORNADA", x, y + 17, CINZA)
            custo_rota, custo_batalhas = self.custo_rota_jornada, self.custo_batalhas_jornada
        else:
            texto(tela, "PLANEJADO", x, y + 17, CINZA)
            custo_rota = self.custo_rota_planejado
            custo_batalhas = self.melhor_custo_sa
        custo_total = (custo_rota + custo_batalhas
                       if custo_rota is not None and custo_batalhas is not None else None)

        linhas = [("C_ROTA", custo_rota, TINTA), ("C_BATALHAS", custo_batalhas, TINTA),
                  ("C_TOTAL", custo_total, VERMELHO)]
        for indice, (rotulo, valor, cor) in enumerate(linhas):
            linha_y = y + 28 + indice * 10
            texto(tela, rotulo, x, linha_y, cor)
            texto(tela, "-" if valor is None else f"{valor:.6f}", direita, linha_y, cor,
                  alinhamento="direita")

        texto(tela, "ESTADOS EXPANDIDOS", x, y + 62, CINZA)
        texto(tela, "A* DA ROTA", x, y + 73)
        texto(tela, f"{self.resultado_rota.expandidos} ({self.resultado_rota.gerados} GER.)",
              direita, y + 73, AZUL, alinhamento="direita")
        texto(tela, "A* GRID (JORNADA)", x, y + 83)
        texto(tela, str(self.expandidos_grid_jornada), direita, y + 83, CIANO, alinhamento="direita")
        texto(tela, "A* GRID (TABELA)", x, y + 93)
        texto(tela, str(self.expandidos_tabela), direita, y + 93, TINTA_FRACA, alinhamento="direita")

        grafico = pygame.Rect(x, y + 106, retangulo.width - 16, 36)
        if len(self.historico_atual) >= 2:
            self._desenhar_grafico_pequeno(tela, grafico)
        else:
            pygame.draw.rect(tela, CINZA_CLARO, grafico)
            texto(tela, "SA AINDA NÃO RODOU", grafico.centerx, grafico.centery - 3, CINZA,
                  alinhamento="centro")

    def _desenhar_grafico_pequeno(self, tela, area):
        """Miniatura da curva do Simulated Annealing no painel de custos.

        Args:
            tela: superfície de destino.
            area: pygame.Rect do gráfico.
        """
        pygame.draw.rect(tela, CINZA_CLARO, area)
        menor, maior = min(self.historico_melhor), max(self.historico_atual)
        amplitude = (maior - menor) or 1.0
        for historico, cor in ((self.historico_atual, CIANO), (self.historico_melhor, LARANJA)):
            pontos = [(int(area.x + 1 + iteracao / config.SA_ITERACOES * (area.width - 3)),
                       int(area.bottom - 2 - (valor - menor) / amplitude * (area.height - 4)))
                      for iteracao, valor in zip(self.historico_iteracoes, historico)]
            pygame.draw.lines(tela, cor, False, pontos)
        texto(tela, "SA", area.x + 3, area.y + 3, TINTA_FRACA, sombra=None)

    def _desenhar_controles(self, tela):
        for acao, retangulo in self.botoes:
            rotulo, tecla, habilitado = self._rotulo_botao(acao)
            if acao == "velocidade":
                texto_claro(tela, rotulo, retangulo.centerx, retangulo.y + 6, alinhamento="centro")
                continue
            sobre = habilitado and retangulo.collidepoint(self.posicao_mouse)
            principal = acao == "alternar" and habilitado
            if not habilitado:
                fundo, cor, cor_tecla = CINZA, TINTA_FRACA, TINTA_FRACA
            elif principal:
                fundo, cor, cor_tecla = AZUL, BRANCO, AZUL_CLARO
            else:
                fundo, cor, cor_tecla = BRANCO, TINTA, TINTA_FRACA
            if sobre:
                fundo = escurecer(fundo, 0.85) if principal else CREME
            deslocamento = 1 if sobre else 0
            pygame.draw.rect(tela, SOMBRA_ESCURA, retangulo.move(0, 2), border_radius=6)
            botao = retangulo.move(0, deslocamento)
            pygame.draw.rect(tela, LARANJA if sobre else CONTORNO_CAIXA, botao, border_radius=6)
            pygame.draw.rect(tela, fundo, botao.inflate(-2, -2), border_radius=5)
            pygame.draw.line(tela, tuple(min(255, componente + 30) for componente in fundo),
                             (botao.x + 4, botao.y + 2), (botao.right - 5, botao.y + 2))
            sombra = None if principal or not habilitado else SOMBRA_TINTA
            largura = largura_texto(rotulo) + (largura_texto(" " + tecla) if tecla else 0)
            inicio = botao.centerx - largura // 2
            inicio += texto(tela, rotulo, inicio, botao.y + 6, cor, sombra=sombra)
            if tecla:
                texto(tela, " " + tecla, inicio, botao.y + 6, cor_tecla, sombra=None)
        texto_claro(tela, "L NOMES  F TELA", TELA_BAIXO.right - 6, CONTROLES_Y + 6, CINZA,
                    alinhamento="direita")


def retangulo_direita(x):
    """Coluna direita dos valores no painel central.

    Args:
        x: x da coluna esquerda do painel central.

    Returns:
        x onde os valores alinhados à direita terminam.
    """
    return x + 234


def ler_argumentos():
    parser = argparse.ArgumentParser(description="INF1771 - Trabalho 1 (interface gráfica)")
    parser.add_argument("--semente", type=int, default=0,
                        help="semente do Simulated Annealing (padrão 0)")
    return parser.parse_args()


def main():
    argumentos = ler_argumentos()
    interface = Interface(argumentos.semente)

    pygame.init()
    pygame.display.set_caption("Kanto - INF1771")
    tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.SCALED)
    relogio = pygame.time.Clock()
    while interface.ativa:
        for evento in pygame.event.get():
            interface.tratar_evento(evento)
        interface.atualizar()
        interface.desenhar(tela)
        pygame.display.flip()
        relogio.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
