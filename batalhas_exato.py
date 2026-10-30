"""
Ótimo exato das batalhas por programação dinâmica (Etapa 6).

Não é a solução pedida pelo enunciado (que exige busca local); serve para
VALIDAR a busca local: com o ótimo exato em mãos, sabemos se o Simulated
Annealing / Hill Climbing chegaram nele ou quanto ficaram longe.

Ideia:
    O custo de cada ginásio só depende dos pokémons escolhidos para ele, e a
    única ligação entre os ginásios é a energia gasta. Então decidimos os
    ginásios um de cada vez, guardando como "estado" quantas vezes cada
    pokémon já lutou:

        estado = (usos do Pikachu, usos do Bulbassauro, ..., usos do Weedle)
                 cada valor entre 0 e 6  ->  no máximo 7^5 = 16 807 estados

        melhor[estado] = menor soma de tempos dos ginásios já decididos
                         que termina exatamente com esses usos

    Para cada ginásio, testamos os 31 times possíveis (todo subconjunto não
    vazio dos 5 pokémons) a partir de cada estado. No fim, entre os estados
    em que pelo menos 1 pokémon tem energia >= 1, pegamos o de menor custo.

    Isso explora todas as escalas possíveis (sem repetir trabalho), então o
    resultado é o ótimo global de C_batalhas.

Poda:
    São no máximo 6*5 - 1 = 29 participações e cada ginásio que falta
    precisa de pelo menos 1. Estados que já usaram tantas participações que
    não sobra 1 para cada ginásio restante são descartados.
"""

import time

import batalhas

TOTAL_GINASIOS = batalhas.TOTAL_GINASIOS
TOTAL_POKEMONS = batalhas.TOTAL_POKEMONS
ENERGIA_INICIAL = batalhas.ENERGIA_INICIAL
MIN_POKEMONS_VIVOS = batalhas.MIN_POKEMONS_VIVOS
INFINITO = float("inf")
TIMES_POSSIVEIS = [
    (mascara, tuple(mascara >> pokemon & 1 for pokemon in range(TOTAL_POKEMONS)))
    for mascara in range(1, 1 << TOTAL_POKEMONS)
]

MAX_PARTICIPACOES = ENERGIA_INICIAL * TOTAL_POKEMONS - MIN_POKEMONS_VIVOS


def otimo_exato():
    """Calcula a escala de batalhas de menor custo possível.

    Returns:
        Tupla (escala, custo, avaliados, tempo): escala ótima, custo ótimo,
        transições avaliadas e tempo gasto em segundos.
    """
    tempo_inicio = time.perf_counter()
    estado_inicial = (0,) * TOTAL_POKEMONS
    camadas = [{estado_inicial: (0.0, None, None)}]
    avaliados = 0

    for ginasio in range(TOTAL_GINASIOS):
        camada_anterior = camadas[-1]
        proxima_camada = {}
        ginasios_restantes = TOTAL_GINASIOS - ginasio - 1
        for estado, (custo_acumulado, _, _) in camada_anterior.items():
            participacoes_ate_agora = sum(estado)
            for mascara, usos_do_time in TIMES_POSSIVEIS:
                novo_estado = tuple(uso + extra for uso, extra in zip(estado, usos_do_time))
                if max(novo_estado) > ENERGIA_INICIAL:
                    continue
                participacoes_previstas = (participacoes_ate_agora
                                           + contar_pokemons(mascara)
                                           + ginasios_restantes)
                if participacoes_previstas > MAX_PARTICIPACOES:
                    continue
                avaliados += 1
                novo_custo = custo_acumulado + batalhas.tempo_batalha(ginasio, mascara)
                custo_ja_conhecido = proxima_camada.get(novo_estado, (INFINITO,))[0]
                if novo_custo < custo_ja_conhecido:
                    proxima_camada[novo_estado] = (novo_custo, estado, mascara)
        camadas.append(proxima_camada)

    estados_finais = {
        estado: dados for estado, dados in camadas[-1].items()
        if batalhas.vivos(estado) >= MIN_POKEMONS_VIVOS
    }
    estado = min(estados_finais, key=lambda estado_final: estados_finais[estado_final][0])
    custo_otimo = estados_finais[estado][0]

    escala = [0] * TOTAL_GINASIOS
    for ginasios_decididos in range(TOTAL_GINASIOS, 0, -1):
        _, estado_anterior, mascara = camadas[ginasios_decididos][estado]
        escala[ginasios_decididos - 1] = mascara
        estado = estado_anterior

    return escala, batalhas.custo(escala), avaliados, time.perf_counter() - tempo_inicio


def contar_pokemons(mascara):
    """Número de pokémons numa máscara.

    Args:
        mascara: máscara de 5 bits.

    Returns:
        Quantidade de bits ligados.
    """
    return bin(mascara).count("1")


# ---------------------------------------------------------------------------
# `python3 batalhas_exato.py`: calcula e mostra o ótimo exato.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    escala_otima, custo_otimo, avaliados, tempo = otimo_exato()
    assert not batalhas.validar(escala_otima), batalhas.validar(escala_otima)
    assert abs(custo_otimo - batalhas.custo(escala_otima)) < 1e-9
    print(f"Ótimo exato por programação dinâmica "
          f"({avaliados} transições, {tempo:.1f}s):")
    batalhas.imprimir_escala(escala_otima)
