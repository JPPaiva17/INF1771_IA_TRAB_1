import argparse

import batalhas
import config
from distancias import carregar_distancias
from mapa import Mapa
from rota import resolver_rota

TOLERANCIA_OTIMO = 1e-6     # diferença máxima para considerar "chegou no ótimo"


def ler_argumentos():
    parser = argparse.ArgumentParser(description="INF1771 - Trabalho 1 (Kanto)")
    parser.add_argument("--algoritmo", choices=["hc", "sa"], default="hc",
                        help="busca local das batalhas: hc = Hill Climbing com "
                             "reinícios (padrão), sa = Simulated Annealing")
    parser.add_argument("--semente", type=int, default=0,
                        help="semente da busca local (padrão 0)")
    parser.add_argument("--sem-exato", action="store_true",
                        help="não calcula o ótimo exato das batalhas para comparar")
    return parser.parse_args()


def titulo(texto):
    print(f"\n{texto}\n{'=' * len(texto)}")


def expandidos_grid(tabela_distancias, ordem_pontos):
    """Nós expandidos pelo A* do grid para montar a tabela de distâncias.

    Os pares ginásio -> ginásio no sentido inverso reaproveitam o caminho
    já calculado, então só contamos cada par uma vez.

    Args:
        tabela_distancias: tabela de distâncias.
        ordem_pontos: símbolos dos pontos na ordem em que foram calculados.

    Returns:
        Total de nós expandidos.
    """
    posicao_do_ponto = {simbolo: posicao for posicao, simbolo in enumerate(ordem_pontos)}
    total_expandidos = 0
    for (partida, chegada), nos_expandidos in tabela_distancias.expandidos.items():
        entre_ginasios = partida in batalhas.GINASIOS and chegada in batalhas.GINASIOS
        if not entre_ginasios or posicao_do_ponto[partida] < posicao_do_ponto[chegada]:
            total_expandidos += nos_expandidos
    return total_expandidos


def custo_inicial():
    """Custo da célula inicial '1', se ela entra na conta (config).

    Returns:
        config.CUSTO_ORIGEM_DESTINO se config.CONTAR_CELULA_INICIAL, senão 0.
    """
    return config.CUSTO_ORIGEM_DESTINO if config.CONTAR_CELULA_INICIAL else 0


def simular(ordem, escala, tabela_distancias):
    """Percorre a rota trecho a trecho aplicando as batalhas.

    Confere na prática que a escala funciona nesta ordem de visita: nenhum
    pokémon luta sem energia.

    Args:
        ordem: símbolos da rota, de '1' até 'U'.
        escala: lista com uma máscara de pokémons por ginásio.
        tabela_distancias: tabela de distâncias.

    Returns:
        Tupla (linhas, custo_rota, custo_batalhas, energia_por_pokemon):
        linhas da tabela da jornada, custo da rota, custo das batalhas e
        dict pokémon -> energia final.

    Raises:
        RuntimeError: se algum pokémon lutar sem energia ou se nenhum chegar
            ao destino com energia.
    """
    energia_por_pokemon = {pokemon: config.ENERGIA_INICIAL for pokemon in batalhas.POKEMONS}
    indice_do_ginasio = {ginasio: indice for indice, ginasio in enumerate(batalhas.GINASIOS)}
    linhas = []
    custo_rota = custo_inicial()
    custo_batalhas = 0.0

    for partida, chegada in zip(ordem, ordem[1:]):
        custo_trecho = tabela_distancias.dist[partida][chegada]
        passos = len(tabela_distancias.caminhos[(partida, chegada)]) - 1
        custo_rota += custo_trecho

        pokemons_na_batalha, tempo_da_batalha = [], 0.0
        if chegada in indice_do_ginasio:
            ginasio = indice_do_ginasio[chegada]
            pokemons_na_batalha = batalhas.nomes(escala[ginasio])
            for pokemon in pokemons_na_batalha:
                if energia_por_pokemon[pokemon] <= 0:
                    raise RuntimeError(f"{pokemon} sem energia no ginásio {chegada}")
                energia_por_pokemon[pokemon] -= 1
            tempo_da_batalha = batalhas.tempo_batalha(ginasio, escala[ginasio])
            custo_batalhas += tempo_da_batalha

        linhas.append((partida, chegada, passos, custo_trecho, pokemons_na_batalha,
                       tempo_da_batalha, custo_rota + custo_batalhas))

    pokemons_vivos = [pokemon for pokemon, energia in energia_por_pokemon.items() if energia >= 1]
    if len(pokemons_vivos) < config.MIN_POKEMONS_VIVOS:
        raise RuntimeError("nenhum pokémon chegou ao destino com energia")
    return linhas, custo_rota, custo_batalhas, energia_por_pokemon


def main():
    argumentos = ler_argumentos()

    titulo("Preparação")
    mapa = Mapa()
    print(f"Mapa {mapa.linhas}x{mapa.colunas} lido de {config.ARQUIVO_MAPA}: "
          f"origem {mapa.origem}, destino {mapa.destino}, "
          f"{len(mapa.ginasios)} ginásios.")
    tabela_distancias = carregar_distancias(mapa)

    resultado_rota = resolver_rota(tabela_distancias)

    if argumentos.algoritmo == "sa":
        nome_algoritmo = "Simulated Annealing"
        resultado_batalhas = batalhas.simulated_annealing(semente=argumentos.semente)
    else:
        nome_algoritmo = f"Hill Climbing com {config.HC_REINICIOS} reinícios"
        resultado_batalhas = batalhas.hill_climbing(semente=argumentos.semente)

    problemas = batalhas.validar(resultado_batalhas.escala)
    if problemas:
        raise RuntimeError("escala inválida: " + "; ".join(problemas))
    print(f"Rota: A* em {resultado_rota.tempo:.2f}s.  Batalhas: {nome_algoritmo} "
          f"(semente {argumentos.semente}) em {resultado_batalhas.tempo:.2f}s.")

    escala = resultado_batalhas.escala
    linhas, custo_rota, custo_batalhas, energia_por_pokemon = simular(
        resultado_rota.ordem, escala, tabela_distancias
    )
    custo_total = custo_rota + custo_batalhas

    titulo("Jornada (custo acumulado a cada trecho)")
    print(f"{'Trecho':<9}{'Passos':>7}{'Caminho':>9}  {'Pokémons na batalha':<34}"
          f"{'Batalha':>12}{'Acumulado':>14}")
    print("-" * 87)
    custo_celula_inicial = custo_inicial()
    print(f"{'início 1':<9}{0:>7}{custo_celula_inicial:>9}  {'(célula inicial)':<34}"
          f"{'':>12}{custo_celula_inicial:>14.6f}")
    for (partida, chegada, passos, custo_trecho, pokemons_na_batalha,
         tempo_da_batalha, acumulado) in linhas:
        texto_pokemons = ", ".join(pokemons_na_batalha) if pokemons_na_batalha else "(chegada)"
        texto_tempo = f"{tempo_da_batalha:12.6f}" if pokemons_na_batalha else f"{'':>12}"
        print(f"{partida + ' -> ' + chegada:<9}{passos:>7}{custo_trecho:>9}  {texto_pokemons:<34}"
              f"{texto_tempo}{acumulado:>14.6f}")

    titulo("Resultado final")
    print("Ordem de visita aos ginásios:")
    print("  " + " -> ".join(resultado_rota.ordem))

    print("\nPokémons usados em cada batalha:")
    indice_do_ginasio = {ginasio: indice for indice, ginasio in enumerate(batalhas.GINASIOS)}
    for numero_visita, ginasio in enumerate(resultado_rota.ginasios, 1):
        indice = indice_do_ginasio[ginasio]
        mascara = escala[indice]
        print(f"  {numero_visita:>2}º  ginásio {ginasio:>2} "
              f"(dificuldade {config.DIFICULDADE[ginasio]:>3}):"
              f" {', '.join(batalhas.nomes(mascara)):<30} "
              f"{batalhas.tempo_batalha(indice, mascara):11.6f} min")

    print("\nEnergia final de cada pokémon:")
    for pokemon, energia in energia_por_pokemon.items():
        print(f"  {pokemon:<12} {energia}")

    print(f"\nCusto das batalhas (C_batalhas): {custo_batalhas:13.6f} min")
    print(f"Custo da rota      (C_rota):     {custo_rota:13.6f} min")
    print(f"Custo total        (C_total):    {custo_total:13.6f} min")

    print(f"\nEstados expandidos pelo A* da rota: {resultado_rota.expandidos} "
          f"(gerados: {resultado_rota.gerados})")
    print(f"Nós expandidos pelo A* do grid para a tabela de distâncias: "
          f"{expandidos_grid(tabela_distancias, list(tabela_distancias.pontos))}")
    print(f"Caminho completo: "
          f"{len(tabela_distancias.caminho_completo(resultado_rota.ordem)) - 1} passos no mapa.")

    if not argumentos.sem_exato:
        from batalhas_exato import otimo_exato
        _, custo_otimo_batalhas, _, _ = otimo_exato()
        titulo("Otimalidade")
        print(f"Rota: ótima (A* com heurística admissível).")
        diferenca = custo_batalhas - custo_otimo_batalhas
        if diferenca < TOLERANCIA_OTIMO:
            print(f"Batalhas: a busca local atingiu o ótimo exato ({custo_otimo_batalhas:.6f}).")
            print(f"C_total = {custo_total:.6f} é o ótimo global.")
        else:
            print(f"Batalhas: {diferenca:.6f} min acima do ótimo exato "
                  f"({custo_otimo_batalhas:.6f}).")
            print(f"Ótimo global seria C_total = {custo_rota + custo_otimo_batalhas:.6f}.")


if __name__ == "__main__":
    main()
