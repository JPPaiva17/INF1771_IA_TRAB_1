import heapq
import math
import time

import config
from distancias import Distancias, carregar_distancias
from mapa import Mapa

INFINITO = float("inf")
BITS_POSICAO = 5
MASCARA_POSICAO = (1 << BITS_POSICAO) - 1
ESTADO_OBJETIVO = -1
INTERVALO_PROGRESSO = 50_000
ITERACOES_HELD_KARP = 30
FATOR_PASSO_INICIAL = 2.0
LIMITE_SEM_MELHORA = 3
FOLGA_ALVO = 1.05
TOLERANCIA = 1e-9


def codificar_estado(posicao, visitados):
    """Junta (posição, visitados) num único inteiro.

    Args:
        posicao: índice do ponto atual (0..n-1 = ginásios, n = origem '1').
        visitados: bitmask dos ginásios já visitados.

    Returns:
        Chave inteira do estado.
    """
    return (visitados << BITS_POSICAO) | posicao


def decodificar_estado(chave):
    """Separa a chave de um estado de volta em (posição, visitados).

    Args:
        chave: chave inteira gerada por codificar_estado().

    Returns:
        Tupla (posicao, visitados).
    """
    return chave & MASCARA_POSICAO, chave >> BITS_POSICAO


class ResultadoRota:
    """Resultado da busca da rota.

    Attributes:
        ordem: símbolos da rota, ['1', g1, g2, ..., g24, 'U'].
        custo: custo da rota (soma dos trechos, sem a célula inicial).
        expandidos: estados expandidos (que tiveram sucessores gerados).
        gerados: estados colocados na fila.
        tempo: tempo da busca, em segundos.
    """

    def __init__(self, ordem, custo, expandidos, gerados, tempo):
        self.ordem = ordem
        self.custo = custo
        self.expandidos = expandidos
        self.gerados = gerados
        self.tempo = tempo

    @property
    def ginasios(self):
        """Só a ordem de visita dos ginásios (sem '1' e 'U')."""
        return self.ordem[1:-1]


class BuscaRota:
    """A* sobre os estados (posição, visitados).

    Internamente os ginásios viram índices 0..n-1 (na ordem recebida) e a
    origem '1' vira o índice n, para usar listas em vez de dicionários
    (bem mais rápido em Python).

    Args:
        tabela_distancias: tabela de distâncias da Etapa 3.
        ginasios: ginásios a visitar. Se None, usa todos (os testes usam
            subconjuntos menores).
        heuristica: 'hk' (Held-Karp, padrão) ou 'mst'.
        iteracoes_hk: iterações de subgradiente do Held-Karp.

    Raises:
        ValueError: se heuristica não for 'hk' nem 'mst'.
    """

    def __init__(self, tabela_distancias: Distancias, ginasios=None, heuristica="hk",
                 iteracoes_hk=ITERACOES_HELD_KARP):
        if heuristica not in ("hk", "mst"):
            raise ValueError("heuristica deve ser 'hk' ou 'mst'")
        self.usar_held_karp = heuristica == "hk"
        self.iteracoes_hk = iteracoes_hk

        self.simbolo_origem = config.SIMBOLO_ORIGEM
        self.simbolo_destino = config.SIMBOLO_DESTINO

        if ginasios is not None:
            self.nomes_ginasios = list(ginasios)
        else:
            self.nomes_ginasios = [
                simbolo for simbolo in tabela_distancias.pontos
                if simbolo not in (self.simbolo_origem, self.simbolo_destino)
            ]

        self.total_ginasios = len(self.nomes_ginasios)
        self.indice_origem = self.total_ginasios
        self.todos_visitados = (1 << self.total_ginasios) - 1

        pontos_de_saida = self.nomes_ginasios + [self.simbolo_origem]
        self.distancias = [
            [tabela_distancias.dist[de][para] if de != para else 0 for para in self.nomes_ginasios]
            for de in pontos_de_saida
        ]

        self.distancias_ate_destino = [
            tabela_distancias.dist[nome][self.simbolo_destino] for nome in self.nomes_ginasios
        ]

        self._cache_mst = {}

    def _indices_restantes(self, restantes):
        """Lista dos índices dos ginásios cujo bit está ligado em `restantes`.

        Args:
            restantes: bitmask de ginásios.

        Returns:
            Lista com os índices dos bits ligados.
        """
        return [indice for indice in range(self.total_ginasios) if restantes & (1 << indice)]

    # ------------------------------------------------------------------
    # Heurística 1: MST
    # ------------------------------------------------------------------
    def _custo_mst(self, indices):
        """Custo da árvore geradora mínima dos ginásios dados (Prim, O(k²)).

        Args:
            indices: índices dos ginásios da árvore.

        Returns:
            Custo total da árvore (0 se houver 1 ginásio ou menos).
        """
        quantidade = len(indices)
        if quantidade <= 1:
            return 0
        distancias = self.distancias

        distancias_do_primeiro = distancias[indices[0]]
        custo_ligacao = [distancias_do_primeiro[ginasio] for ginasio in indices]
        na_arvore = [False] * quantidade
        na_arvore[0] = True
        custo_total = 0

        for _ in range(quantidade - 1):
            escolhido = min(
                (posicao for posicao in range(quantidade) if not na_arvore[posicao]),
                key=lambda posicao: custo_ligacao[posicao],
            )
            na_arvore[escolhido] = True
            custo_total += custo_ligacao[escolhido]

            distancias_do_escolhido = distancias[indices[escolhido]]
            for posicao in range(quantidade):
                distancia = distancias_do_escolhido[indices[posicao]]
                if not na_arvore[posicao] and distancia < custo_ligacao[posicao]:
                    custo_ligacao[posicao] = distancia

        return custo_total

    def heuristica_mst(self, posicao, visitados):
        """Heurística MST: MST(R) + menor dist(posição, R) + menor dist(R, 'U').

        R é o conjunto de ginásios que ainda faltam visitar.

        Args:
            posicao: índice do ponto atual (n = origem '1').
            visitados: bitmask dos ginásios já visitados.

        Returns:
            Limite inferior do custo restante até 'U'.
        """
        restantes = self.todos_visitados ^ visitados
        if restantes == 0:
            return self.distancias_ate_destino[posicao]

        parte_fixa = self._cache_mst.get(restantes)
        if parte_fixa is None:
            indices = self._indices_restantes(restantes)
            menor_chegada_em_u = min(self.distancias_ate_destino[indice] for indice in indices)
            parte_fixa = self._custo_mst(indices) + menor_chegada_em_u
            self._cache_mst[restantes] = parte_fixa

        distancias_da_posicao = self.distancias[posicao]
        menor_saida = min(
            distancias_da_posicao[indice]
            for indice in range(self.total_ginasios) if restantes & (1 << indice)
        )
        return parte_fixa + menor_saida

    # ------------------------------------------------------------------
    # Heurística 2: Held-Karp (MST com pesos ajustados)
    # ------------------------------------------------------------------
    def heuristica_held_karp(self, posicao, visitados, alvo=None):
        """Maior limite inferior L(pesos) encontrado em algumas iterações de subgradiente.

        Cada ginásio recebe um peso que é somado a toda aresta que toca nele.
        Ginásios com muitas ligações na árvore ficam mais caros e folhas ficam
        mais baratas, até a árvore se parecer com um caminho.

        Args:
            posicao: índice do ponto atual (n = origem '1').
            visitados: bitmask dos ginásios já visitados.
            alvo: estimativa do custo real restante (se conhecida), usada só
                para dimensionar o tamanho do passo. Qualquer valor dos pesos
                dá um limite válido, então o passo não afeta a correção, só a
                qualidade.

        Returns:
            Limite inferior do custo restante até 'U', arredondado para cima
            e nunca menor que a heurística MST.
        """
        restantes = self.todos_visitados ^ visitados
        if restantes == 0:
            return self.distancias_ate_destino[posicao]

        indices = self._indices_restantes(restantes)
        quantidade = len(indices)
        distancias = self.distancias
        distancias_da_posicao = distancias[posicao]

        if quantidade == 1:
            unico = indices[0]
            return distancias_da_posicao[unico] + self.distancias_ate_destino[unico]

        distancias_entre_restantes = [[distancias[de][para] for para in indices] for de in indices]
        distancias_saindo_da_posicao = [distancias_da_posicao[indice] for indice in indices]
        distancias_chegando_em_u = [self.distancias_ate_destino[indice] for indice in indices]

        pesos = [0.0] * quantidade
        melhor_limite = -INFINITO
        fator_passo = FATOR_PASSO_INICIAL
        iteracoes_sem_melhora = 0

        for _ in range(self.iteracoes_hk):
            grau = [0] * quantidade
            na_arvore = [False] * quantidade
            na_arvore[0] = True
            primeira_linha = distancias_entre_restantes[0]
            peso_primeiro = pesos[0]
            custo_ligacao = [
                primeira_linha[outro] + peso_primeiro + pesos[outro] for outro in range(quantidade)
            ]
            ligado_a = [0] * quantidade
            custo_arvore = 0.0

            for _ in range(quantidade - 1):
                escolhido, menor_ligacao = -1, INFINITO
                for candidato in range(quantidade):
                    if not na_arvore[candidato] and custo_ligacao[candidato] < menor_ligacao:
                        escolhido, menor_ligacao = candidato, custo_ligacao[candidato]

                na_arvore[escolhido] = True
                custo_arvore += menor_ligacao
                grau[escolhido] += 1
                grau[ligado_a[escolhido]] += 1

                distancias_do_escolhido = distancias_entre_restantes[escolhido]
                peso_escolhido = pesos[escolhido]
                for candidato in range(quantidade):
                    if not na_arvore[candidato]:
                        custo_modificado = (distancias_do_escolhido[candidato]
                                            + peso_escolhido + pesos[candidato])
                        if custo_modificado < custo_ligacao[candidato]:
                            custo_ligacao[candidato] = custo_modificado
                            ligado_a[candidato] = escolhido

            primeiro_ginasio = min(
                range(quantidade), key=lambda indice: distancias_saindo_da_posicao[indice] + pesos[indice]
            )
            ultimo_ginasio = min(
                range(quantidade), key=lambda indice: distancias_chegando_em_u[indice] + pesos[indice]
            )
            grau[primeiro_ginasio] += 1
            grau[ultimo_ginasio] += 1

            limite = (custo_arvore
                      + distancias_saindo_da_posicao[primeiro_ginasio] + pesos[primeiro_ginasio]
                      + distancias_chegando_em_u[ultimo_ginasio] + pesos[ultimo_ginasio]
                      - 2 * sum(pesos))

            if limite > melhor_limite + TOLERANCIA:
                melhor_limite = limite
                iteracoes_sem_melhora = 0
            else:
                iteracoes_sem_melhora += 1
                if iteracoes_sem_melhora >= LIMITE_SEM_MELHORA:
                    fator_passo /= 2
                    iteracoes_sem_melhora = 0

            subgradiente = [grau_ginasio - 2 for grau_ginasio in grau]
            norma_quadrada = sum(valor * valor for valor in subgradiente)
            if norma_quadrada == 0:
                break

            if alvo is not None and alvo > limite:
                custo_alvo = alvo
            else:
                custo_alvo = limite * FOLGA_ALVO + 1
            tamanho_passo = fator_passo * (custo_alvo - limite) / norma_quadrada
            pesos = [pesos[indice] + tamanho_passo * subgradiente[indice]
                     for indice in range(quantidade)]

        return max(math.ceil(melhor_limite), self.heuristica_mst(posicao, visitados))

    # ------------------------------------------------------------------
    # Solução inicial (limite superior)
    # ------------------------------------------------------------------
    def rota_gulosa(self):
        """Rota rápida, não necessariamente ótima.

        Vizinho mais próximo, melhorada com 2-opt (inverter trechos enquanto
        o custo cair). Serve só como limite superior para descartar estados
        inúteis.

        Returns:
            Tupla (ordem, custo): ordem dos índices dos ginásios e custo da
            rota completa de '1' até 'U'.
        """
        distancias = self.distancias
        distancias_ate_destino = self.distancias_ate_destino

        ordem = []
        atual = self.indice_origem
        faltam = set(range(self.total_ginasios))
        while faltam:
            distancias_do_atual = distancias[atual]
            atual = min(faltam, key=lambda ginasio: distancias_do_atual[ginasio])
            ordem.append(atual)
            faltam.remove(atual)

        def custo_da_ordem(ordem_ginasios):
            custo = distancias[self.indice_origem][ordem_ginasios[0]]
            for de, para in zip(ordem_ginasios, ordem_ginasios[1:]):
                custo += distancias[de][para]
            custo += distancias_ate_destino[ordem_ginasios[-1]]
            return custo

        melhor_custo = custo_da_ordem(ordem)
        melhorou = True
        while melhorou:
            melhorou = False
            for inicio in range(self.total_ginasios - 1):
                for fim in range(inicio + 1, self.total_ginasios):
                    trecho_invertido = ordem[inicio:fim + 1][::-1]
                    nova_ordem = ordem[:inicio] + trecho_invertido + ordem[fim + 1:]
                    novo_custo = custo_da_ordem(nova_ordem)
                    if novo_custo < melhor_custo:
                        ordem, melhor_custo, melhorou = nova_ordem, novo_custo, True

        return ordem, melhor_custo

    # ------------------------------------------------------------------
    # A*
    # ------------------------------------------------------------------
    def resolver(self, verbose=False):
        """Executa o A* e devolve a rota ótima.

        Args:
            verbose: se True, imprime o progresso da busca.

        Returns:
            ResultadoRota com a rota ótima.
        """
        tempo_inicio = time.perf_counter()
        distancias = self.distancias
        distancias_ate_destino = self.distancias_ate_destino
        todos_visitados = self.todos_visitados

        ordem_gulosa, limite_superior = self.rota_gulosa()
        if verbose:
            print(f"  limite superior (vizinho mais próximo + 2-opt): {limite_superior}")

        estado_inicial = codificar_estado(self.indice_origem, 0)

        melhor_custo = {estado_inicial: 0}
        veio_de = {estado_inicial: None}

        estimativa_inicial = self.heuristica_mst(self.indice_origem, 0)
        fila = [(estimativa_inicial, 0, estado_inicial, not self.usar_held_karp)]
        gerados = 1
        expandidos = 0
        proximo_progresso = INTERVALO_PROGRESSO

        while fila:
            custo_estimado, menos_custo_ate_aqui, estado, ja_refinado = heapq.heappop(fila)
            custo_ate_aqui = -menos_custo_ate_aqui

            if custo_ate_aqui > melhor_custo.get(estado, INFINITO):
                continue
            if estado == ESTADO_OBJETIVO:
                break

            posicao, visitados = decodificar_estado(estado)

            if not ja_refinado:
                estimativa_restante = self.heuristica_held_karp(
                    posicao, visitados, alvo=limite_superior - custo_ate_aqui
                )
                if custo_ate_aqui + estimativa_restante > custo_estimado:
                    custo_estimado = custo_ate_aqui + estimativa_restante
                    if custo_estimado <= limite_superior:
                        heapq.heappush(fila, (custo_estimado, menos_custo_ate_aqui, estado, True))
                    continue

            expandidos += 1
            if verbose and expandidos >= proximo_progresso:
                print(f"  {expandidos:>9} expandidos | fila {len(fila):>9} | "
                      f"f = {custo_estimado:.0f} | {time.perf_counter() - tempo_inicio:.1f}s")
                proximo_progresso += INTERVALO_PROGRESSO

            if visitados == todos_visitados:
                custo_com_destino = custo_ate_aqui + distancias_ate_destino[posicao]
                if custo_com_destino < melhor_custo.get(ESTADO_OBJETIVO, INFINITO):
                    melhor_custo[ESTADO_OBJETIVO] = custo_com_destino
                    veio_de[ESTADO_OBJETIVO] = estado
                    heapq.heappush(fila, (custo_com_destino, -custo_com_destino,
                                          ESTADO_OBJETIVO, True))
                    gerados += 1
                continue

            distancias_da_posicao = distancias[posicao]
            for proximo in range(self.total_ginasios):
                if visitados & (1 << proximo):
                    continue

                visitados_depois = visitados | (1 << proximo)
                estado_vizinho = codificar_estado(proximo, visitados_depois)
                custo_vizinho = custo_ate_aqui + distancias_da_posicao[proximo]
                if custo_vizinho >= melhor_custo.get(estado_vizinho, INFINITO):
                    continue

                estimado_vizinho = max(
                    custo_estimado,
                    custo_vizinho + self.heuristica_mst(proximo, visitados_depois),
                )
                if estimado_vizinho > limite_superior:
                    continue

                melhor_custo[estado_vizinho] = custo_vizinho
                veio_de[estado_vizinho] = estado
                heapq.heappush(fila, (estimado_vizinho, -custo_vizinho, estado_vizinho,
                                      not self.usar_held_karp))
                gerados += 1

        if ESTADO_OBJETIVO in veio_de:
            ordem = self._reconstruir_ordem(veio_de)
            custo_rota = melhor_custo[ESTADO_OBJETIVO]
        else:
            ordem = ([self.simbolo_origem]
                     + [self.nomes_ginasios[indice] for indice in ordem_gulosa]
                     + [self.simbolo_destino])
            custo_rota = limite_superior

        return ResultadoRota(ordem, custo_rota, expandidos, gerados,
                             time.perf_counter() - tempo_inicio)

    def _reconstruir_ordem(self, veio_de):
        """Segue os estados anteriores a partir do objetivo e monta a rota.

        Args:
            veio_de: dict estado -> estado anterior no melhor caminho.

        Returns:
            Lista de símbolos da rota, de '1' até 'U'.
        """
        ordem = [self.simbolo_destino]
        estado = veio_de[ESTADO_OBJETIVO]
        while estado is not None:
            posicao, _ = decodificar_estado(estado)
            if posicao == self.indice_origem:
                ordem.append(self.simbolo_origem)
            else:
                ordem.append(self.nomes_ginasios[posicao])
            estado = veio_de[estado]
        ordem.reverse()
        return ordem


def resolver_rota(tabela_distancias: Distancias, ginasios=None, heuristica="hk",
                  verbose=False):
    """Atalho: monta a busca e resolve.

    Args:
        tabela_distancias: tabela de distâncias da Etapa 3.
        ginasios: ginásios a visitar. Se None, usa todos.
        heuristica: 'hk' (Held-Karp, padrão) ou 'mst'.
        verbose: se True, imprime o progresso da busca.

    Returns:
        ResultadoRota com a rota ótima.
    """
    busca = BuscaRota(tabela_distancias, ginasios, heuristica)
    return busca.resolver(verbose=verbose)


# ---------------------------------------------------------------------------
# `python3 rota.py`: resolve a rota completa e mostra o resultado.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mapa = Mapa()
    tabela_distancias = carregar_distancias(mapa)

    print("\nResolvendo a rota pelos 24 ginásios com A*...")
    resultado = resolver_rota(tabela_distancias, verbose=True)

    custo_celula_inicial = config.CUSTO_ORIGEM_DESTINO if config.CONTAR_CELULA_INICIAL else 0
    print(f"\nOrdem de visita: {' -> '.join(resultado.ordem)}")
    print(f"Custo da rota (C_rota): {resultado.custo + custo_celula_inicial} "
          f"(trechos {resultado.custo} + célula inicial {custo_celula_inicial})")
    print(f"Estados expandidos: {resultado.expandidos}   gerados: {resultado.gerados}   "
          f"tempo: {resultado.tempo:.1f}s")

    # Conferências: a rota visita cada ginásio uma vez, o custo bate com a
    # tabela e com a soma do terreno do caminho completo célula a célula.
    assert sorted(resultado.ginasios) == sorted(mapa.ginasios), "ginásios faltando/repetidos"
    assert resultado.custo == tabela_distancias.custo_ordem(resultado.ordem)
    caminho = tabela_distancias.caminho_completo(resultado.ordem)
    custo_celula_a_celula = sum(mapa.custo(linha, coluna) for linha, coluna in caminho[1:])
    assert resultado.custo == custo_celula_a_celula
    print(f"Caminho completo: {len(caminho) - 1} passos, "
          f"custo conferido célula a célula.")

    print("\nTrechos:")
    acumulado = custo_celula_inicial
    for partida, chegada in zip(resultado.ordem, resultado.ordem[1:]):
        custo_trecho = tabela_distancias.dist[partida][chegada]
        acumulado += custo_trecho
        print(f"  {partida} -> {chegada}: {custo_trecho:>4}   acumulado {acumulado:>5}")
