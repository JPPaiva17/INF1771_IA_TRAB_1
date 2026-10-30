import math
import random
import time

import config

GINASIOS = list(config.DIFICULDADE)
POKEMONS = list(config.PODER)
DIFICULDADES = [config.DIFICULDADE[ginasio] for ginasio in GINASIOS]
PODERES = [config.PODER[pokemon] for pokemon in POKEMONS]
TOTAL_GINASIOS = len(GINASIOS)
TOTAL_POKEMONS = len(POKEMONS)
ENERGIA_INICIAL = config.ENERGIA_INICIAL
MIN_POKEMONS_VIVOS = config.MIN_POKEMONS_VIVOS

PODER_POR_MASCARA = [
    sum(PODERES[pokemon] for pokemon in range(TOTAL_POKEMONS) if mascara >> pokemon & 1)
    for mascara in range(1 << TOTAL_POKEMONS)
]

MOVIMENTO_ADICIONAR = 0
MOVIMENTO_REMOVER = 1
MOVIMENTO_TROCAR = 2
MOVIMENTO_MOVER = 3
MOVIMENTO_PERMUTAR = 4
TOTAL_TIPOS_MOVIMENTO = 5

TOLERANCIA = 1e-12
INTERVALO_HISTORICO = 500


def tempo_batalha(ginasio, mascara):
    """Tempo da batalha no ginásio dado com os pokémons da máscara.

    Args:
        ginasio: índice do ginásio (ordem da Tabela 1).
        mascara: máscara de 5 bits com os pokémons que lutam.

    Returns:
        Dificuldade do ginásio dividida pela soma dos poderes.
    """
    return DIFICULDADES[ginasio] / PODER_POR_MASCARA[mascara]


def custo(escala):
    """C_batalhas: soma dos tempos das 24 batalhas.

    Args:
        escala: lista com uma máscara de pokémons por ginásio.

    Returns:
        Soma dos tempos de todas as batalhas.
    """
    return sum(tempo_batalha(ginasio, mascara) for ginasio, mascara in enumerate(escala))


def usos(escala):
    """Quantas batalhas cada pokémon luta.

    Args:
        escala: lista com uma máscara de pokémons por ginásio.

    Returns:
        Lista com o número de batalhas de cada pokémon (ordem da Tabela 2).
    """
    return [
        sum(mascara >> pokemon & 1 for mascara in escala)
        for pokemon in range(TOTAL_POKEMONS)
    ]


def energia_final(escala):
    """Energia de cada pokémon ao chegar no destino.

    Args:
        escala: lista com uma máscara de pokémons por ginásio.

    Returns:
        Lista com a energia final de cada pokémon (ordem da Tabela 2).
    """
    return [ENERGIA_INICIAL - uso for uso in usos(escala)]


def vivos(usos_por_pokemon):
    """Quantos pokémons terminam com energia >= 1 dada a contagem de usos.

    Args:
        usos_por_pokemon: número de batalhas de cada pokémon.

    Returns:
        Quantidade de pokémons que chegam com energia.
    """
    return sum(uso <= ENERGIA_INICIAL - 1 for uso in usos_por_pokemon)


def validar(escala):
    """Lista de problemas da escala (vazia se ela for válida).

    Args:
        escala: lista com uma máscara de pokémons por ginásio.

    Returns:
        Lista de mensagens descrevendo cada restrição quebrada.
    """
    problemas = []
    if len(escala) != TOTAL_GINASIOS:
        problemas.append(f"escala com {len(escala)} ginásios; esperado {TOTAL_GINASIOS}")

    for ginasio, mascara in enumerate(escala):
        if mascara == 0:
            problemas.append(f"ginásio {GINASIOS[ginasio]} sem pokémon")

    usos_por_pokemon = usos(escala)
    for pokemon, uso in enumerate(usos_por_pokemon):
        if uso > ENERGIA_INICIAL:
            problemas.append(f"{POKEMONS[pokemon]} luta {uso} vezes (máx. {ENERGIA_INICIAL})")

    if vivos(usos_por_pokemon) < MIN_POKEMONS_VIVOS:
        problemas.append(f"menos de {MIN_POKEMONS_VIVOS} pokémon chega com energia")
    return problemas


def nomes(mascara):
    """Nomes dos pokémons de uma máscara.

    Args:
        mascara: máscara de 5 bits.

    Returns:
        Lista com os nomes dos pokémons cujo bit está ligado.
    """
    return [POKEMONS[pokemon] for pokemon in range(TOTAL_POKEMONS) if mascara >> pokemon & 1]


def escala_aleatoria(rng):
    """Escala inicial válida, sorteada.

    Cada ginásio recebe 1 pokémon sorteado entre os que ainda têm energia.
    São 24 usos para 30 de energia, então sobra energia e pelo menos um
    pokémon termina vivo.

    Args:
        rng: gerador de números aleatórios (random.Random).

    Returns:
        Escala válida com 1 pokémon por ginásio.
    """
    while True:
        usos_por_pokemon = [0] * TOTAL_POKEMONS
        escala = []
        for _ in range(TOTAL_GINASIOS):
            com_energia = [
                pokemon for pokemon in range(TOTAL_POKEMONS)
                if usos_por_pokemon[pokemon] < ENERGIA_INICIAL
            ]
            sorteado = rng.choice(com_energia)
            usos_por_pokemon[sorteado] += 1
            escala.append(1 << sorteado)

        if vivos(usos_por_pokemon) >= MIN_POKEMONS_VIVOS:
            return escala


def pode_usar(usos_por_pokemon, pokemon, batalhas_extras=1):
    """Diz se o pokémon pode lutar mais `batalhas_extras` vez(es) sem quebrar regras.

    Args:
        usos_por_pokemon: número de batalhas de cada pokémon.
        pokemon: índice do pokémon.
        batalhas_extras: quantas batalhas a mais ele lutaria.

    Returns:
        True se as restrições de energia continuam valendo.
    """
    usos_atuais = usos_por_pokemon[pokemon]
    if usos_atuais + batalhas_extras > ENERGIA_INICIAL:
        return False

    if usos_atuais <= ENERGIA_INICIAL - 1 < usos_atuais + batalhas_extras:
        return vivos(usos_por_pokemon) - 1 >= MIN_POKEMONS_VIVOS
    return True


def vizinhos(escala, usos_por_pokemon):
    """Gera TODOS os movimentos válidos (usado pelo Hill Climbing).

    Args:
        escala: escala atual.
        usos_por_pokemon: número de batalhas de cada pokémon na escala atual.

    Yields:
        Tuplas (alteracoes, pokemon_que_ganha, pokemon_que_perde): a lista
        [(ginasio, nova_mascara)], o pokémon que passa a lutar uma vez a mais
        e o que passa a lutar uma vez a menos (ou None).
    """
    for ginasio, mascara in enumerate(escala):
        for pokemon in range(TOTAL_POKEMONS):
            bit_pokemon = 1 << pokemon

            if mascara & bit_pokemon:
                mascara_sem_pokemon = mascara ^ bit_pokemon

                if mascara != bit_pokemon:
                    yield [(ginasio, mascara_sem_pokemon)], None, pokemon

                    for outro_ginasio, mascara_outro in enumerate(escala):
                        if outro_ginasio != ginasio and not mascara_outro & bit_pokemon:
                            yield [
                                (ginasio, mascara_sem_pokemon),
                                (outro_ginasio, mascara_outro | bit_pokemon),
                            ], None, None

                for outro_pokemon in range(TOTAL_POKEMONS):
                    if mascara >> outro_pokemon & 1:
                        continue
                    bit_outro_pokemon = 1 << outro_pokemon

                    if pode_usar(usos_por_pokemon, outro_pokemon):
                        yield [
                            (ginasio, mascara_sem_pokemon | bit_outro_pokemon)
                        ], outro_pokemon, pokemon

                    for outro_ginasio in range(ginasio + 1, TOTAL_GINASIOS):
                        mascara_outro = escala[outro_ginasio]
                        if mascara_outro & bit_outro_pokemon and not mascara_outro & bit_pokemon:
                            yield [
                                (ginasio, mascara_sem_pokemon | bit_outro_pokemon),
                                (outro_ginasio, (mascara_outro ^ bit_outro_pokemon) | bit_pokemon),
                            ], None, None

            elif pode_usar(usos_por_pokemon, pokemon):
                yield [(ginasio, mascara | bit_pokemon)], pokemon, None


def vizinho_aleatorio(escala, usos_por_pokemon, rng):
    """Sorteia UM movimento válido (usado pelo Simulated Annealing).

    Args:
        escala: escala atual.
        usos_por_pokemon: número de batalhas de cada pokémon na escala atual.
        rng: gerador de números aleatórios (random.Random).

    Returns:
        Tupla (alteracoes, pokemon_que_ganha, pokemon_que_perde), no mesmo
        formato de vizinhos().
    """
    while True:
        tipo = rng.randrange(TOTAL_TIPOS_MOVIMENTO)
        ginasio = rng.randrange(TOTAL_GINASIOS)
        mascara = escala[ginasio]
        pokemon = rng.randrange(TOTAL_POKEMONS)
        bit_pokemon = 1 << pokemon

        if tipo == MOVIMENTO_ADICIONAR:
            if not mascara & bit_pokemon and pode_usar(usos_por_pokemon, pokemon):
                return [(ginasio, mascara | bit_pokemon)], pokemon, None

        elif tipo == MOVIMENTO_REMOVER:
            if mascara & bit_pokemon and mascara != bit_pokemon:
                return [(ginasio, mascara ^ bit_pokemon)], None, pokemon

        elif tipo == MOVIMENTO_TROCAR:
            outro_pokemon = rng.randrange(TOTAL_POKEMONS)
            if (mascara & bit_pokemon and not mascara >> outro_pokemon & 1
                    and pode_usar(usos_por_pokemon, outro_pokemon)):
                nova_mascara = (mascara ^ bit_pokemon) | (1 << outro_pokemon)
                return [(ginasio, nova_mascara)], outro_pokemon, pokemon

        elif tipo == MOVIMENTO_MOVER:
            outro_ginasio = rng.randrange(TOTAL_GINASIOS)
            if (outro_ginasio != ginasio and mascara & bit_pokemon and mascara != bit_pokemon
                    and not escala[outro_ginasio] & bit_pokemon):
                return [
                    (ginasio, mascara ^ bit_pokemon),
                    (outro_ginasio, escala[outro_ginasio] | bit_pokemon),
                ], None, None

        else:
            outro_ginasio = rng.randrange(TOTAL_GINASIOS)
            outro_pokemon = rng.randrange(TOTAL_POKEMONS)
            bit_outro_pokemon = 1 << outro_pokemon
            mascara_outro = escala[outro_ginasio]
            if (outro_ginasio != ginasio and mascara & bit_pokemon and not mascara & bit_outro_pokemon
                    and mascara_outro & bit_outro_pokemon and not mascara_outro & bit_pokemon):
                return [
                    (ginasio, (mascara ^ bit_pokemon) | bit_outro_pokemon),
                    (outro_ginasio, (mascara_outro ^ bit_outro_pokemon) | bit_pokemon),
                ], None, None


def delta(escala, alteracoes):
    """Variação do custo se as alterações forem aplicadas.

    Args:
        escala: escala atual.
        alteracoes: lista [(ginasio, nova_mascara), ...].

    Returns:
        Custo novo menos custo atual (negativo = melhora).
    """
    return sum(
        tempo_batalha(ginasio, nova_mascara) - tempo_batalha(ginasio, escala[ginasio])
        for ginasio, nova_mascara in alteracoes
    )


def aplicar(escala, usos_por_pokemon, movimento):
    alteracoes, pokemon_que_ganha, pokemon_que_perde = movimento
    for ginasio, nova_mascara in alteracoes:
        escala[ginasio] = nova_mascara

    if pokemon_que_ganha is not None:
        usos_por_pokemon[pokemon_que_ganha] += 1
    if pokemon_que_perde is not None:
        usos_por_pokemon[pokemon_que_perde] -= 1


class ResultadoBatalhas:
    def __init__(self, escala, custo, tempo, historico=None):
        self.escala = escala
        self.custo = custo
        self.tempo = tempo
        self.historico = historico

    @property
    def energia_final(self):
        return energia_final(self.escala)


def simulated_annealing(semente=None,
                        temperatura_inicial=config.SA_TEMPERATURA_INICIAL,
                        temperatura_final=config.SA_TEMPERATURA_FINAL,
                        iteracoes=config.SA_ITERACOES):
    """Simulated Annealing com resfriamento geométrico.

    A cada iteração sorteia um vizinho:
        - se ele é melhor (variação < 0), aceita;
        - se é pior, aceita com probabilidade exp(-variação / temperatura).
    Com temperatura alta no início, a busca aceita pioras e escapa de ótimos
    locais; a temperatura cai até temperatura_final e no fim a busca só
    aceita melhoras.

    Args:
        semente: semente do gerador aleatório (None = aleatória).
        temperatura_inicial: temperatura no começo da busca.
        temperatura_final: temperatura no fim da busca.
        iteracoes: número de iterações.

    Returns:
        ResultadoBatalhas com a melhor escala encontrada.
    """
    tempo_inicio = time.perf_counter()
    rng = random.Random(semente)
    escala = escala_aleatoria(rng)
    usos_por_pokemon = usos(escala)
    custo_atual = custo(escala)
    melhor_custo, melhor_escala = custo_atual, escala[:]
    historico = []

    fator_resfriamento = (temperatura_final / temperatura_inicial) ** (1 / iteracoes)
    temperatura = temperatura_inicial
    for iteracao in range(iteracoes):
        movimento = vizinho_aleatorio(escala, usos_por_pokemon, rng)
        variacao = delta(escala, movimento[0])

        if variacao < 0 or rng.random() < math.exp(-variacao / temperatura):
            aplicar(escala, usos_por_pokemon, movimento)
            custo_atual += variacao
            if custo_atual < melhor_custo - TOLERANCIA:
                melhor_custo, melhor_escala = custo_atual, escala[:]

        temperatura *= fator_resfriamento
        if iteracao % INTERVALO_HISTORICO == 0:
            historico.append(melhor_custo)

    return ResultadoBatalhas(melhor_escala, custo(melhor_escala),
                             time.perf_counter() - tempo_inicio, historico)


def hill_climbing(semente=None, reinicios=config.HC_REINICIOS):
    """Hill Climbing (subida mais íngreme) com reinícios aleatórios.

    A partir de uma escala aleatória, olha TODOS os vizinhos e vai para o
    melhor, enquanto houver melhora. Quando nenhum vizinho melhora, está num
    ótimo local: guarda o resultado e recomeça de outra escala aleatória.

    Args:
        semente: semente do gerador aleatório (None = aleatória).
        reinicios: quantas subidas fazer, cada uma de uma escala aleatória.

    Returns:
        ResultadoBatalhas com a melhor escala encontrada.
    """
    tempo_inicio = time.perf_counter()
    rng = random.Random(semente)
    melhor_custo, melhor_escala = math.inf, None
    historico = []

    for _ in range(reinicios):
        escala = escala_aleatoria(rng)
        usos_por_pokemon = usos(escala)
        custo_atual = custo(escala)

        while True:
            melhor_movimento, melhor_variacao = None, -TOLERANCIA
            for movimento in vizinhos(escala, usos_por_pokemon):
                variacao = delta(escala, movimento[0])
                if variacao < melhor_variacao:
                    melhor_movimento, melhor_variacao = movimento, variacao

            if melhor_movimento is None:
                break

            aplicar(escala, usos_por_pokemon, melhor_movimento)
            custo_atual += melhor_variacao

        if custo_atual < melhor_custo:
            melhor_custo, melhor_escala = custo_atual, escala[:]
        historico.append(melhor_custo)

    return ResultadoBatalhas(melhor_escala, custo(melhor_escala),
                             time.perf_counter() - tempo_inicio, historico)


def imprimir_escala(escala):
    """Imprime uma tabela com os pokémons e o tempo de cada batalha.

    Args:
        escala: lista com uma máscara de pokémons por ginásio.
    """
    for ginasio, mascara in enumerate(escala):
        print(f"  {GINASIOS[ginasio]:>2} (dif {DIFICULDADES[ginasio]:>3}): "
              f"{', '.join(nomes(mascara)):<45} {tempo_batalha(ginasio, mascara):8.3f}")

    energias = ", ".join(
        f"{POKEMONS[pokemon]}={energia}"
        for pokemon, energia in enumerate(energia_final(escala))
    )
    print("  Energia final: " + energias)
    print(f"  C_batalhas = {custo(escala):.4f}")


if __name__ == "__main__":
    algoritmos = (("Simulated Annealing", simulated_annealing),
                  ("Hill Climbing com reinícios", hill_climbing))
    for nome_algoritmo, algoritmo in algoritmos:
        resultado = algoritmo(semente=0)
        assert not validar(resultado.escala), validar(resultado.escala)
        print(f"\n{nome_algoritmo}  ({resultado.tempo:.2f}s)")
        imprimir_escala(resultado.escala)
