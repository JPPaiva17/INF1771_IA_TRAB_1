import csv
import statistics
import sys

import batalhas
import config
from batalhas_exato import otimo_exato

ARQUIVO_CSV = "experimentos.csv"
TOLERANCIA = 1e-6     # diferença máxima para considerar "chegou no ótimo"

ALGORITMOS = {
    "Simulated Annealing": lambda semente: batalhas.simulated_annealing(semente),
    "Hill Climbing (1 subida)": lambda semente: batalhas.hill_climbing(semente, reinicios=1),
    f"Hill Climbing ({config.HC_REINICIOS} reinícios)":
        lambda semente: batalhas.hill_climbing(semente, reinicios=config.HC_REINICIOS),
}


def rodar(execucoes=30):
    escala_otima, custo_otimo, _, _ = otimo_exato()
    print(f"Ótimo exato (programação dinâmica): {custo_otimo:.4f}\n")

    linhas_csv = []
    resumo = {}
    melhores_resultados = {}

    for nome_algoritmo, algoritmo in ALGORITMOS.items():
        custos, tempos = [], []
        melhor_resultado = None
        for indice_execucao in range(execucoes):
            semente = indice_execucao
            resultado = algoritmo(semente)
            assert not batalhas.validar(resultado.escala), (
                nome_algoritmo, semente, batalhas.validar(resultado.escala))
            custos.append(resultado.custo)
            tempos.append(resultado.tempo)
            if melhor_resultado is None or resultado.custo < melhor_resultado.custo:
                melhor_resultado = resultado
            linhas_csv.append({
                "algoritmo": nome_algoritmo,
                "execucao": indice_execucao + 1,
                "semente": semente,
                "custo": f"{resultado.custo:.6f}",
                "diferenca_otimo": f"{resultado.custo - custo_otimo:.6f}",
                "atingiu_otimo": int(resultado.custo - custo_otimo < TOLERANCIA),
                "tempo_s": f"{resultado.tempo:.4f}",
            })

        execucoes_no_otimo = sum(custo - custo_otimo < TOLERANCIA for custo in custos)
        resumo[nome_algoritmo] = {
            "melhor": min(custos),
            "media": statistics.mean(custos),
            "desvio": statistics.stdev(custos) if len(custos) > 1 else 0.0,
            "pior": max(custos),
            "acertos": execucoes_no_otimo,
            "tempo": statistics.mean(tempos),
        }
        melhores_resultados[nome_algoritmo] = melhor_resultado
        print(f"  {nome_algoritmo}: {execucoes} execuções concluídas")

    with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8") as arquivo_csv:
        escritor = csv.DictWriter(arquivo_csv, fieldnames=list(linhas_csv[0]))
        escritor.writeheader()
        escritor.writerows(linhas_csv)

    print(f"\nResultados ({execucoes} execuções por algoritmo, "
          f"ótimo = {custo_otimo:.4f}):\n")
    cabecalho = (f"{'Algoritmo':<28} {'Melhor':>10} {'Média':>10} {'Desvio':>8} "
                 f"{'Pior':>10} {'Ótimo':>9} {'Tempo médio':>12}")
    print(cabecalho)
    print("-" * len(cabecalho))
    for nome_algoritmo, estatisticas in resumo.items():
        print(f"{nome_algoritmo:<28} {estatisticas['melhor']:>10.4f} "
              f"{estatisticas['media']:>10.4f} {estatisticas['desvio']:>8.4f} "
              f"{estatisticas['pior']:>10.4f} "
              f"{estatisticas['acertos']:>4}/{execucoes:<4} {estatisticas['tempo']:>11.3f}s")

    print(f"\nExecuções individuais salvas em {ARQUIVO_CSV}.")

    melhor_sa = melhores_resultados["Simulated Annealing"]
    print(f"\nMelhor escala do Simulated Annealing "
          f"(diferença para o ótimo: {melhor_sa.custo - custo_otimo:.4f}):")
    batalhas.imprimir_escala(melhor_sa.escala)
    if melhor_sa.custo - custo_otimo >= TOLERANCIA:
        print("\nEscala ótima (programação dinâmica):")
        batalhas.imprimir_escala(escala_otima)

    return resumo


if __name__ == "__main__":
    rodar(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
