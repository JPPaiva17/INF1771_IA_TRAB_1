import heapq
from mapa import Mapa

# Considerações importantes:
#    - O treinador só anda na VERTICAL e HORIZONTAL
#    - Outros ginásios: pisar em um ginásio obriga a batalhar, e cada ginásio é batalhado uma única vez.
#    - A jornada termina ao chegar em U, então ele só pode ser pisado no último trecho.


def heuristica(linha, coluna, linha_destino, coluna_destino, custo_destino):
    """
    Distância Manhattan: Estimativa do custo de (linha, coluna) até o destino.
        h = (Manhattan - 1) + custo_destino

    Por quê:
        - Sem diagonal, são necessários pelo menos Manhattan passos.
        - Os Manhattan - 1 passos intermediários custam no mínimo 1 cada (o terreno mais barato, '.', custa 1).
        - O último passo é entrar no destino, que custa exatamente custo_destino (0 para ginásio, 1 para U).

    Admissível e consistente: cada passo reduz a Manhattan em no máximo 1 e custa no mínimo 1 => A* encontra o ótimo.

    Args:
        linha:          linha da célula atual.
        coluna:         coluna da célula atual.
        linha_destino:  linha do destino.
        coluna_destino: coluna do destino.
        custo_destino:  custo para entrar na célula de destino.

    Returns:
        Limite inferior do custo de (linha, coluna) até o destino.
    """
    manhattan = abs(linha - linha_destino) + abs(coluna - coluna_destino)
    if manhattan == 0:
        return 0

    return (manhattan - 1) + custo_destino


def obstaculos_padrao(mapa: Mapa, destino):
    """
    Todos os ginásios e o U, exceto o próprio destino do trecho.

    Args:
        mapa: objeto Mapa.
        destino: (linha, coluna) do destino do trecho.

    Returns:
        Conjunto de células que o trecho não pode pisar.
    """
    obstaculos = set()
    for posicao in mapa.posicoes_ginasios:
        obstaculos.add(posicao)

    obstaculos.add(mapa.destino)
    if destino in obstaculos:
        obstaculos.remove(destino)

    return obstaculos


def astar(mapa: Mapa, origem, destino, obstaculos=None, registro=None, usar_heuristica=True):
    """
    Caminho de menor custo de origem até destino.

    Args:
        mapa:               objeto Mapa.
        origem:             (linha, coluna) de partida.
        destino:            (linha, coluna) de chegada.
        obstaculos:         conjunto de células proibidas. Se None, usa
                            obstaculos_padrao() (outros ginásios e U).

        registro:           dict opcional. Se for passado, é preenchido com
                            'expandidos' (lista das células na ordem em que foram
                            expandidas) e 'fronteira' (conjunto de células que ainda
                            estavam na fila ao terminar). Não pesa quando é None.

        usar_heuristica:    False transforma o A* em Dijkstra (h = 0). Usado
                            só nos testes, para comparar e confirmar a otimalidade.

    Returns:
        Tupla (custo, caminho, nos_expandidos):
            custo:          soma dos custos das células ENTRADAS (a célula de
                            origem não é contada); inf se não houver caminho.

            caminho:        lista de (linha, coluna) da origem até o destino, inclusive.

            nos_expandidos: quantas células foram expandidas.
    """

    if obstaculos is None:
        obstaculos = obstaculos_padrao(mapa, destino)

    linha_destino, coluna_destino = destino
    custo_destino = mapa.custo(linha_destino, coluna_destino)

    def h(linha, coluna):
        if not usar_heuristica:
            return 0
        return heuristica(linha, coluna, linha_destino, coluna_destino, custo_destino)

    linha_origem, coluna_origem = origem
    fila = [(h(linha_origem, coluna_origem), 0, linha_origem, coluna_origem)]
    melhor_g = {origem: 0}
    veio_de = {origem: None}
    fechados = set()
    expandidos = [] if registro is not None else None

    while fila:
        f, g, linha, coluna = heapq.heappop(fila)
        celula = (linha, coluna)

        if celula in fechados:
            continue
        fechados.add(celula)

        if expandidos is not None:
            expandidos.append(celula)

        # Objetivo: como a heurística é consistente, este g é o ótimo.
        if celula == destino:
            if registro is not None:
                _preencher_registro(registro, expandidos, fila, fechados)
            return g, _reconstruir_caminho(veio_de, destino), len(fechados)

        # Gera os sucessores: cima, baixo, esquerda, direita.
        for linha_vizinho, coluna_vizinho in mapa.vizinhos(linha, coluna):
            vizinho = (linha_vizinho, coluna_vizinho)
            if vizinho in obstaculos or vizinho in fechados:
                continue

            novo_g = g + mapa.custo(linha_vizinho, coluna_vizinho)

            # Só empilha se for o melhor caminho já encontrado até o vizinho.
            if novo_g < melhor_g.get(vizinho, float("inf")):
                melhor_g[vizinho] = novo_g
                veio_de[vizinho] = celula
                novo_f = novo_g + h(linha_vizinho, coluna_vizinho)
                heapq.heappush(fila, (novo_f, novo_g, linha_vizinho, coluna_vizinho))

    # A fila esvaziou sem chegar ao destino: não existe caminho.
    if registro is not None:
        _preencher_registro(registro, expandidos, fila, fechados)
    return float("inf"), [], len(fechados)


def _reconstruir_caminho(veio_de, destino):
    """
    Segue os pais do destino até a origem e inverte a lista.

    Args:
        veio_de: dict célula -> célula anterior no melhor caminho.
        destino: célula final do caminho.

    Returns:
        Lista de células da origem até o destino, inclusive.
    """
    caminho = []
    celula = destino
    while celula is not None:
        caminho.append(celula)
        celula = veio_de[celula]
    caminho.reverse()
    return caminho


def _preencher_registro(registro, expandidos, fila, fechados):
    """
    Guarda a ordem de expansão e a fronteira final (sem duplicatas).

    Args:
        registro: dict que recebe as chaves 'expandidos' e 'fronteira'.
        expandidos: células na ordem em que foram expandidas.
        fila: fila de prioridade no fim da busca.
        fechados: células já expandidas.
    """
    registro["expandidos"] = expandidos
    registro["fronteira"] = {(linha, coluna) for _, _, linha, coluna in fila} - fechados