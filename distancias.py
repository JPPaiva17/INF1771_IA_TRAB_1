import hashlib
import os
import pickle
import time
import config
from astar_grid import astar
from mapa import Mapa

ARQUIVO_CACHE = "distancias.pkl"

class Distancias:
    """
    Resultado da Etapa 3.

    Attributes:
        pontos: dict símbolo -> (linha, coluna), na ordem '1', ginásios, 'U'.
        dist: dist[a][b] = custo do melhor caminho de a até b.
        caminhos: caminhos[(a, b)] = lista de (linha, coluna) de a até b, inclusive.
        expandidos: expandidos[(a, b)] = nós expandidos pelo A* nesse
            trecho (nos pares invertidos repete o valor do par calculado).
        assinatura: identifica o mapa/config usados (validação do cache).
    """

    def __init__(self, pontos, assinatura):
        self.pontos = pontos
        self.assinatura = assinatura
        self.dist = {a: {} for a in pontos}
        self.caminhos = {}
        self.expandidos = {}

    def registrar(self, a, b, custo, caminho, n_expandidos):
        """Guarda o resultado do trecho a -> b.

        Args:
            a: símbolo do ponto de partida.
            b: símbolo do ponto de chegada.
            custo: custo do trecho.
            caminho: lista de (linha, coluna) de a até b, inclusive.
            n_expandidos: nós expandidos pelo A* no trecho.
        """
        self.dist[a][b] = custo
        self.caminhos[(a, b)] = caminho
        self.expandidos[(a, b)] = n_expandidos

    def caminho_completo(self, ordem):
        """Junta os trechos de uma sequência de pontos em um único caminho.

        Cada trecho começa na célula onde o anterior terminou, então essa
        célula é pulada para não repetir.

        Args:
            ordem: sequência de símbolos, ex.: ['1', '2', '3', ..., 'U'].

        Returns:
            Lista de (linha, coluna) do primeiro ao último ponto da sequência.
        """
        caminho = [self.pontos[ordem[0]]]
        for a, b in zip(ordem, ordem[1:]):
            caminho.extend(self.caminhos[(a, b)][1:])
        return caminho

    def custo_ordem(self, ordem):
        """Soma das distâncias de uma sequência de pontos (custo da rota).

        Args:
            ordem: sequência de símbolos, ex.: ['1', '2', '3', ..., 'U'].

        Returns:
            Soma de dist[a][b] para cada par consecutivo da sequência.
        """
        return sum(self.dist[a][b] for a, b in zip(ordem, ordem[1:]))


def pontos_de_interesse(mapa: Mapa):
    """Origem, os 24 ginásios (ordem da Tabela 1) e o destino.

    Args:
        mapa: objeto Mapa.

    Returns:
        dict símbolo -> (l, c).
    """
    return {config.SIMBOLO_ORIGEM: mapa.origem,
            **mapa.ginasios,
            config.SIMBOLO_DESTINO: mapa.destino}


def assinatura(mapa: Mapa):
    """Resumo (hash) de tudo que influencia as distâncias: o mapa e os custos.

    Se qualquer um mudar, a assinatura muda e o cache deixa de valer.

    Args:
        mapa: objeto Mapa.

    Returns:
        Hash SHA-256 em hexadecimal.
    """
    dados = repr((mapa.grid, sorted(config.CUSTO_TERRENO.items()),
                  config.CUSTO_ORIGEM_DESTINO, config.CUSTO_GINASIO,
                  sorted(config.DIFICULDADE)))
    return hashlib.sha256(dados.encode("utf-8")).hexdigest()


def calcular_distancias(mapa: Mapa):
    """Roda o A* para todos os pares necessários e monta a tabela.

    Args:
        mapa: objeto Mapa.

    Returns:
        Objeto Distancias preenchido.

    Raises:
        ValueError: se algum par de pontos não tiver caminho.
    """
    pontos = pontos_de_interesse(mapa)
    d = Distancias(pontos, assinatura(mapa))
    origem, destino = config.SIMBOLO_ORIGEM, config.SIMBOLO_DESTINO
    ginasios = list(mapa.ginasios)

    def trecho(a, b):
        custo, caminho, n = astar(mapa, pontos[a], pontos[b])
        if not caminho:
            raise ValueError(f"Não existe caminho de '{a}' para '{b}'.")
        d.registrar(a, b, custo, caminho, n)
        return custo, caminho, n

    # 1) Origem -> cada ginásio.
    for g in ginasios:
        trecho(origem, g)

    # 2) Ginásio <-> ginásio: calcula a -> b e reaproveita invertido em b -> a.
    for i, a in enumerate(ginasios):
        for b in ginasios[i + 1:]:
            custo, caminho, n = trecho(a, b)
            d.registrar(b, a, custo, caminho[::-1], n)

    # 3) Cada ginásio -> destino.
    for g in ginasios:
        trecho(g, destino)

    return d


def carregar_distancias(mapa: Mapa, arquivo=ARQUIVO_CACHE, verbose=True):
    """Devolve a tabela de distâncias, usando o cache se ele for válido.

    Caso contrário calcula tudo de novo e regrava o cache.

    Args:
        mapa: objeto Mapa.
        arquivo: caminho do arquivo de cache.
        verbose: se True, imprime de onde vieram as distâncias.

    Returns:
        Objeto Distancias.
    """
    assin = assinatura(mapa)

    if os.path.exists(arquivo):
        try:
            with open(arquivo, "rb") as f:
                d = pickle.load(f)
            if isinstance(d, Distancias) and d.assinatura == assin:
                if verbose:
                    print(f"Distâncias carregadas do cache ({arquivo}).")
                return d
            if verbose:
                print("Cache desatualizado (mapa ou custos mudaram); recalculando.")
        except Exception:
            if verbose:
                print("Cache ilegível; recalculando.")

    inicio = time.perf_counter()
    d = calcular_distancias(mapa)
    if verbose:
        print(f"Distâncias calculadas em {time.perf_counter() - inicio:.1f}s "
              f"({len(d.caminhos)} trechos).")

    with open(arquivo, "wb") as f:
        pickle.dump(d, f)
    return d