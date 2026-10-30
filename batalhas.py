import math
import random
import time

import config

GINASIOS = list(config.DIFICULDADE)
POKEMONS = list(config.PODER)
DIFIC = [config.DIFICULDADE[g] for g in GINASIOS]
PODER = [config.PODER[p] for p in POKEMONS]
N_G, N_P = len(GINASIOS), len(POKEMONS)
ENERGIA = config.ENERGIA_INICIAL
MIN_VIVOS = config.MIN_POKEMONS_VIVOS

PODER_MASCARA = [sum(PODER[p] for p in range(N_P) if m >> p & 1)
                 for m in range(1 << N_P)]


def tempo_batalha(g, mascara):
    """Tempo da batalha no ginásio g com os pokémons da máscara.

    Args:
        g: índice do ginásio (ordem da Tabela 1).
        mascara: máscara de 5 bits com os pokémons que lutam.

    Returns:
        Dificuldade do ginásio dividida pela soma dos poderes.
    """
    return DIFIC[g] / PODER_MASCARA[mascara]


def custo(escala):
    """C_batalhas: soma dos tempos das 24 batalhas.

    Args:
        escala: lista com uma máscara de pokémons por ginásio.

    Returns:
        Soma dos tempos de todas as batalhas.
    """
    return sum(tempo_batalha(g, m) for g, m in enumerate(escala))


def usos(escala):
    """Quantas batalhas cada pokémon luta.

    Args:
        escala: lista com uma máscara de pokémons por ginásio.

    Returns:
        Lista com o número de batalhas de cada pokémon (ordem da Tabela 2).
    """
    return [sum(m >> p & 1 for m in escala) for p in range(N_P)]


def energia_final(escala):
    """Energia de cada pokémon ao chegar no destino.

    Args:
        escala: lista com uma máscara de pokémons por ginásio.

    Returns:
        Lista com a energia final de cada pokémon (ordem da Tabela 2).
    """
    return [ENERGIA - u for u in usos(escala)]


def vivos(contagem):
    """Quantos pokémons terminam com energia >= 1 dada a contagem de usos.

    Args:
        contagem: número de batalhas de cada pokémon.

    Returns:
        Quantidade de pokémons que chegam com energia.
    """
    return sum(u <= ENERGIA - 1 for u in contagem)


def validar(escala):
    """Lista de problemas da escala (vazia se ela for válida).

    Args:
        escala: lista com uma máscara de pokémons por ginásio.

    Returns:
        Lista de mensagens descrevendo cada restrição quebrada.
    """
    problemas = []
    if len(escala) != N_G:
        problemas.append(f"escala com {len(escala)} ginásios; esperado {N_G}")
    for g, m in enumerate(escala):
        if m == 0:
            problemas.append(f"ginásio {GINASIOS[g]} sem pokémon")
    contagem = usos(escala)
    for p, u in enumerate(contagem):
        if u > ENERGIA:
            problemas.append(f"{POKEMONS[p]} luta {u} vezes (máx. {ENERGIA})")
    if vivos(contagem) < MIN_VIVOS:
        problemas.append(f"menos de {MIN_VIVOS} pokémon chega com energia")
    return problemas


def nomes(mascara):
    """Nomes dos pokémons de uma máscara.

    Args:
        mascara: máscara de 5 bits.

    Returns:
        Lista com os nomes dos pokémons cujo bit está ligado.
    """
    return [POKEMONS[p] for p in range(N_P) if mascara >> p & 1]


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
        contagem = [0] * N_P
        escala = []
        for _ in range(N_G):
            p = rng.choice([p for p in range(N_P) if contagem[p] < ENERGIA])
            contagem[p] += 1
            escala.append(1 << p)
        if vivos(contagem) >= MIN_VIVOS:
            return escala


def pode_usar(contagem, p, extra=1):
    """Diz se o pokémon p pode lutar mais `extra` vez(es) sem quebrar regras.

    Args:
        contagem: número de batalhas de cada pokémon.
        p: índice do pokémon.
        extra: quantas batalhas a mais ele lutaria.

    Returns:
        True se as restrições de energia continuam valendo.
    """
    if contagem[p] + extra > ENERGIA:
        return False
    if contagem[p] <= ENERGIA - 1 < contagem[p] + extra:
        return vivos(contagem) - 1 >= MIN_VIVOS
    return True


def vizinhos(escala, contagem):
    """Gera TODOS os movimentos válidos (usado pelo Hill Climbing).

    Args:
        escala: escala atual.
        contagem: número de batalhas de cada pokémon na escala atual.

    Yields:
        Tuplas (alteracoes, p_ganha, p_perde): a lista [(g, nova_mascara)],
        o pokémon que passa a lutar uma vez a mais e o que passa a lutar uma
        vez a menos (ou None).
    """
    for g, m in enumerate(escala):
        for p in range(N_P):
            bit = 1 << p
            if m & bit:
                if m != bit:
                    yield [(g, m ^ bit)], None, p
                    for h, mh in enumerate(escala):
                        if h != g and not mh & bit:
                            yield [(g, m ^ bit), (h, mh | bit)], None, None
                for q in range(N_P):
                    if m >> q & 1:
                        continue
                    if pode_usar(contagem, q):
                        yield [(g, (m ^ bit) | (1 << q))], q, p
                    bq = 1 << q
                    for h in range(g + 1, N_G):
                        mh = escala[h]
                        if mh & bq and not mh & bit:
                            yield ([(g, (m ^ bit) | bq), (h, (mh ^ bq) | bit)],
                                   None, None)
            elif pode_usar(contagem, p):
                yield [(g, m | bit)], p, None


def vizinho_aleatorio(escala, contagem, rng):
    """Sorteia UM movimento válido (usado pelo Simulated Annealing).

    Args:
        escala: escala atual.
        contagem: número de batalhas de cada pokémon na escala atual.
        rng: gerador de números aleatórios (random.Random).

    Returns:
        Tupla (alteracoes, p_ganha, p_perde), no mesmo formato de vizinhos().
    """
    while True:
        tipo = rng.randrange(5)
        g = rng.randrange(N_G)
        m = escala[g]
        p = rng.randrange(N_P)
        bit = 1 << p
        if tipo == 0:
            if not m & bit and pode_usar(contagem, p):
                return [(g, m | bit)], p, None
        elif tipo == 1:
            if m & bit and m != bit:
                return [(g, m ^ bit)], None, p
        elif tipo == 2:
            q = rng.randrange(N_P)
            if m & bit and not m >> q & 1 and pode_usar(contagem, q):
                return [(g, (m ^ bit) | (1 << q))], q, p
        elif tipo == 3:
            h = rng.randrange(N_G)
            if h != g and m & bit and m != bit and not escala[h] & bit:
                return [(g, m ^ bit), (h, escala[h] | bit)], None, None
        else:
            h = rng.randrange(N_G)
            q = rng.randrange(N_P)
            bq = 1 << q
            mh = escala[h]
            if (h != g and m & bit and not m & bq
                    and mh & bq and not mh & bit):
                return [(g, (m ^ bit) | bq), (h, (mh ^ bq) | bit)], None, None


def delta(escala, alteracoes):
    """Variação do custo se as alterações forem aplicadas.

    Args:
        escala: escala atual.
        alteracoes: lista [(g, nova_mascara), ...].

    Returns:
        Custo novo menos custo atual (negativo = melhora).
    """
    return sum(tempo_batalha(g, nova) - tempo_batalha(g, escala[g])
               for g, nova in alteracoes)


def aplicar(escala, contagem, movimento):
    alteracoes, ganha, perde = movimento
    for g, nova in alteracoes:
        escala[g] = nova
    if ganha is not None:
        contagem[ganha] += 1
    if perde is not None:
        contagem[perde] -= 1


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
                        t_inicial=config.SA_TEMPERATURA_INICIAL,
                        t_final=config.SA_TEMPERATURA_FINAL,
                        iteracoes=config.SA_ITERACOES):
    """Simulated Annealing com resfriamento geométrico.

    A cada iteração sorteia um vizinho:
        - se ele é melhor (delta < 0), aceita;
        - se é pior, aceita com probabilidade exp(-delta / T).
    Com T alto no início, a busca aceita pioras e escapa de ótimos locais;
    T cai até t_final e no fim a busca só aceita melhoras.

    Args:
        semente: semente do gerador aleatório (None = aleatória).
        t_inicial: temperatura inicial.
        t_final: temperatura final.
        iteracoes: número de iterações.

    Returns:
        ResultadoBatalhas com a melhor escala encontrada.
    """
    inicio = time.perf_counter()
    rng = random.Random(semente)
    escala = escala_aleatoria(rng)
    contagem = usos(escala)
    atual = custo(escala)
    melhor, melhor_escala = atual, escala[:]
    historico = []

    alfa = (t_final / t_inicial) ** (1 / iteracoes)
    T = t_inicial
    for it in range(iteracoes):
        mov = vizinho_aleatorio(escala, contagem, rng)
        d = delta(escala, mov[0])
        if d < 0 or rng.random() < math.exp(-d / T):
            aplicar(escala, contagem, mov)
            atual += d
            if atual < melhor - 1e-12:
                melhor, melhor_escala = atual, escala[:]
        T *= alfa
        if it % 500 == 0:
            historico.append(melhor)

    return ResultadoBatalhas(melhor_escala, custo(melhor_escala),
                             time.perf_counter() - inicio, historico)


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
    inicio = time.perf_counter()
    rng = random.Random(semente)
    melhor, melhor_escala = math.inf, None
    historico = []

    for _ in range(reinicios):
        escala = escala_aleatoria(rng)
        contagem = usos(escala)
        atual = custo(escala)
        while True:
            melhor_mov, melhor_d = None, -1e-12
            for mov in vizinhos(escala, contagem):
                d = delta(escala, mov[0])
                if d < melhor_d:
                    melhor_mov, melhor_d = mov, d
            if melhor_mov is None:
                break
            aplicar(escala, contagem, melhor_mov)
            atual += melhor_d
        if atual < melhor:
            melhor, melhor_escala = atual, escala[:]
        historico.append(melhor)

    return ResultadoBatalhas(melhor_escala, custo(melhor_escala),
                             time.perf_counter() - inicio, historico)


def imprimir_escala(escala):
    """Imprime uma tabela com os pokémons e o tempo de cada batalha.

    Args:
        escala: lista com uma máscara de pokémons por ginásio.
    """
    for g, m in enumerate(escala):
        print(f"  {GINASIOS[g]:>2} (dif {DIFIC[g]:>3}): "
              f"{', '.join(nomes(m)):<45} {tempo_batalha(g, m):8.3f}")
    print("  Energia final: " + ", ".join(
        f"{POKEMONS[p]}={e}" for p, e in enumerate(energia_final(escala))))
    print(f"  C_batalhas = {custo(escala):.4f}")


if __name__ == "__main__":
    for nome, alg in (("Simulated Annealing", simulated_annealing),
                      ("Hill Climbing com reinícios", hill_climbing)):
        r = alg(semente=0)
        assert not validar(r.escala), validar(r.escala)
        print(f"\n{nome}  ({r.tempo:.2f}s)")
        imprimir_escala(r.escala)
