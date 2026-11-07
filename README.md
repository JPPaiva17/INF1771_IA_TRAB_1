# INF1771 – Trabalho 1: Jornada por Kanto

Aluno: João Pedro Paiva
Matrícula: 2110569
Link do Vídeo: 

O treinador sai de **1**, precisa vencer os **24 ginásios** em qualquer ordem e chegar ao **U**, no menor tempo possível. O trabalho tem duas partes:

- **Rota:** em que ordem visitar os ginásios. Resolvida com **A\***.
- **Batalhas:** quais pokémons lutam em cada ginásio. Resolvida com **busca local** (Simulated Annealing e Hill Climbing).

O objetivo é minimizar `C_total = C_rota + C_batalhas`.

## Resultado

| | Valor | Garantia |
|---|---|---|
| C_rota | 1076 | ótimo (A* com heurística admissível) |
| C_batalhas | 1484.675006 | igual ao ótimo exato calculado por programação dinâmica |
| **C_total** | **2560.675006** | ótimo global |

Ordem de visita: `1 → O → 3 → I → 4 → 7 → 6 → 5 → S → T → 9 → 8 → B → D → C → E → G → H → L → N → K → J → 2 → P → Q → U`

Energia final: Pikachu 0, Bulbassauro 0, Rattata 0, Caterpie 0, Weedle 1.

## Respostas do formulário

### Melhor resultado: custo total

**C_total = 2560.675006 min** (C_rota 1076 + C_batalhas 1484.675006)

### Melhor resultado: custo das batalhas (só a combinatória, pela busca local)

**C_batalhas = 1484.675006 min**, encontrado pelo Simulated Annealing e pelo Hill Climbing. É o mesmo valor do ótimo exato calculado por programação dinâmica (`batalhas_exato.py`).

### Experimento da busca local

Cada algoritmo foi executado **1000 vezes** (sementes 0 a 999), **3000 execuções no total**. As execuções individuais estão em `experimentos.csv`.

| Algoritmo | Execuções | Média do custo | Desvio-padrão | Melhor | Atingiu o ótimo |
|---|---|---|---|---|---|
| Simulated Annealing | 1000 | 1484.675006 | 0.000000 | 1484.675006 | 1000/1000 |
| Hill Climbing (1 subida) | 1000 | 1484.675006 | 0.000000 | 1484.675006 | 1000/1000 |
| Hill Climbing (20 reinícios) | 1000 | 1484.675006 | 0.000000 | 1484.675006 | 1000/1000 |

Com a vizinhança inicial, sem o movimento "trocar times", a média e o desvio eram: SA 1490.030973 ± 4.839381, HC com 1 subida 1491.271829 ± 4.411945 e HC com 20 reinícios 1484.939209 ± 0.644844.

### Lista de pokémons para cada ginásio

Na ordem da Tabela 1 do enunciado. A coluna "Visita" é a posição do ginásio na rota.

| Ginásio | Dificuldade | Visita | Pokémons | Σ Poder | Tempo (min) |
|---|---|---|---|---|---|
| 2 | 35 | 22º | Weedle | 1.1 | 31.818182 |
| 3 | 40 | 2º | Caterpie | 1.2 | 33.333333 |
| 4 | 45 | 4º | Caterpie | 1.2 | 37.500000 |
| 5 | 50 | 7º | Rattata | 1.3 | 38.461538 |
| 6 | 55 | 6º | Rattata | 1.3 | 42.307692 |
| 7 | 60 | 5º | Rattata | 1.3 | 46.153846 |
| 8 | 65 | 11º | Rattata | 1.3 | 50.000000 |
| 9 | 70 | 10º | Bulbassauro | 1.4 | 50.000000 |
| B | 75 | 12º | Bulbassauro | 1.4 | 53.571429 |
| C | 80 | 14º | Bulbassauro | 1.4 | 57.142857 |
| D | 85 | 13º | Bulbassauro | 1.4 | 60.714286 |
| E | 90 | 15º | Bulbassauro | 1.4 | 64.285714 |
| G | 95 | 16º | Bulbassauro | 1.4 | 67.857143 |
| H | 100 | 17º | Pikachu | 1.5 | 66.666667 |
| I | 110 | 3º | Pikachu | 1.5 | 73.333333 |
| J | 120 | 21º | Pikachu | 1.5 | 80.000000 |
| K | 130 | 20º | Pikachu | 1.5 | 86.666667 |
| L | 140 | 18º | Pikachu | 1.5 | 93.333333 |
| N | 150 | 19º | Pikachu | 1.5 | 100.000000 |
| O | 155 | 1º | Caterpie, Weedle | 2.3 | 67.391304 |
| P | 160 | 23º | Caterpie, Weedle | 2.3 | 69.565217 |
| Q | 165 | 24º | Caterpie, Weedle | 2.3 | 71.739130 |
| S | 170 | 8º | Rattata, Weedle | 2.4 | 70.833333 |
| T | 180 | 9º | Rattata, Caterpie | 2.5 | 72.000000 |
| **Total** | | | | | **1484.675006** |

Batalhas por pokémon: Pikachu 6, Bulbassauro 6, Rattata 6, Caterpie 6, Weedle 5, e o Weedle chega ao U com 1 de energia.

## Ordem dos ginásios 

Ordem de visita: `1 → O → 3 → I → 4 → 7 → 6 → 5 → S → T → 9 → 8 → B → D → C → E → G → H → L → N → K → J → 2 → P → Q → U`


## Como a solução está organizada

A rota e as batalhas são **independentes**. O tempo de um ginásio depende só de quem luta nele, e a regra de energia limita apenas o **total** de batalhas de cada pokémon (no máximo 6, com pelo menos 1 sobrando). Se uma escala respeita esse total, ela funciona em qualquer ordem de visita. Por isso cada parte é otimizada separadamente, e a soma dos dois ótimos é o ótimo global.

```
kanto.txt ─► mapa.py ─► astar_grid.py ─► distancias.py ─► rota.py ─────────┐
                         (A* no grid)    (tabela 26×26)   (A* nos estados) ├─► main.py / interface.py
config.py ─────────────────────────────────────────────► batalhas.py ──────┘   (jornada e resultado)
                                                          (SA e HC)
                                                          batalhas_exato.py (validação)
```

## Arquivos

### Dados e configuração

| Arquivo | O que tem |
|---|---|
| `kanto.txt` | O mapa 150 × 42. Cada caractere é um terreno (`M`, `A`, `F`, `R`, `.`), um ginásio (`2`…`T`), a origem `1` ou o destino `U`. Pode ser editado à vontade. |
| `config.py` | Tudo o que é configurável: custo de cada terreno, custo da origem/destino (+1), custo de pisar num ginásio (0, porque só a batalha conta), dificuldade dos ginásios, poder dos pokémons, energia inicial (6), mínimo de pokémons vivos (1) e os parâmetros do SA e do HC. |

### Rota (Tarefa 2)

| Arquivo | O que faz |
|---|---|
| `mapa.py` | Classe `Mapa`: lê e valida o `kanto.txt`, localiza a origem, o destino e os 24 ginásios, informa o custo de entrar em cada célula e lista os vizinhos (só vertical e horizontal). |
| `astar_grid.py` | A* entre duas células do mapa. **Estado:** a célula. **Custo:** custo de entrar na célula. **Heurística:** `h = (Manhattan − 1) + custo do destino`, que é admissível e consistente. Os outros ginásios e o U são obstáculos, porque pisar num ginásio obriga a batalhar. Pode registrar a ordem de expansão e a fronteira, que a interface usa para desenhar a busca. |
| `distancias.py` | Monta a tabela de menor custo entre os 26 pontos (origem, 24 ginásios e destino) com 324 chamadas do A*. Ginásio ↔ ginásio é calculado uma vez e reaproveitado no sentido inverso. Também guarda os caminhos e os nós expandidos de cada trecho. |
| `distancias.pkl` | Cache da tabela. Ele leva uma assinatura (hash) do mapa e dos custos e é recalculado sozinho quando algum deles muda. |
| `rota.py` | A* que escolhe a ordem dos ginásios. **Estado:** (posição atual, conjunto de ginásios visitados), com o conjunto guardado em 24 bits. **Ações:** ir para um ginásio ainda não visitado; com todos visitados, ir para U. **Heurísticas:** MST dos ginásios restantes e **Held-Karp** (MST com pesos ajustados por subgradiente), ambas limites inferiores. Usa um limite superior (vizinho mais próximo + 2-opt) para podar. Expande 37 estados. |

### Batalhas (Tarefa 1)

| Arquivo | O que faz |
|---|---|
| `batalhas.py` | Busca local das batalhas. **Representação:** a *escala*, com uma máscara de 5 bits por ginásio dizendo quem luta. **Custo:** `Σ dificuldade / Σ poder do time`. **Restrições:** pelo menos 1 pokémon por ginásio, no máximo 6 batalhas por pokémon e pelo menos 1 vivo no fim. A solução inicial é válida e a **vizinhança só gera escalas válidas** (adicionar, remover, trocar, mover, permutar, trocar times), então não há penalidade. Implementa o **Simulated Annealing** (resfriamento geométrico de T=10 até 0.001 em 50.000 iterações) e o **Hill Climbing** (subida mais íngreme com 20 reinícios). A variação de custo de cada movimento é calculada só nos ginásios alterados. |
| `batalhas_exato.py` | Ótimo exato das batalhas por **programação dinâmica**: decide um ginásio por vez, guardando quantas vezes cada pokémon já lutou (no máximo 7⁵ estados). Não é a solução pedida, porque o enunciado exige busca local; serve para **validar** que o SA e o HC chegaram no ótimo global. |

### Execução, experimentos e apresentação

| Arquivo | O que faz |
|---|---|
| `main.py` | Programa principal em modo texto. Resolve a rota e as batalhas, simula a jornada trecho a trecho (conferindo a energia) e mostra o que o enunciado pede: ordem de visita, pokémons de cada batalha, energia final, C_batalhas, C_rota, C_total e estados expandidos. No fim compara com o ótimo exato. |
| `experimentos.py` | Roda SA, HC (1 subida) e HC (20 reinícios) várias vezes com sementes diferentes e mostra melhor, média, desvio-padrão, pior, quantas vezes atingiu o ótimo e o tempo médio. |
| `experimentos.csv` | Resultado de 1000 execuções por algoritmo: os três atingiram 1484.675006 em 1000/1000, com desvio 0. |
| `interface.py` | Interface gráfica em pygame, com visual pixelado de duas telas. Roda os algoritmos ao vivo e permite iniciar, pausar, avançar um passo ou uma etapa. Mostra a ordem achada pelo A* da rota, o SA convergindo (com gráfico e zoom perto do mínimo), o A* expandindo células em cada trecho (expandidos, fronteira e caminho final), o treinador andando, as batalhas, a energia e os custos atualizados enquanto ele anda, e o resumo final. Ao terminar, confere se tudo bate com `main.simular`. |
| `apresentacao.html` | Slides do vídeo. Abra no navegador, use ← / → para navegar e F para tela cheia. |
| `roteiro_video.md` | Falas de cada slide, passo a passo da demonstração da interface e perguntas prováveis. |

## Executando

```bash
python3 main.py                  # resultado em texto (busca local padrão: HC com reinícios)
python3 main.py --algoritmo sa   # usando Simulated Annealing
python3 interface.py             # interface gráfica (precisa do pygame)
python3 experimentos.py 1000     # experimentos; ATENÇÃO: sobrescreve experimentos.csv
python3 rota.py                  # só a rota, com as conferências de custo
python3 batalhas.py              # só as batalhas (SA e HC)
python3 batalhas_exato.py        # só o ótimo exato das batalhas
```

`main.py` e `interface.py` aceitam `--semente N` para mudar a semente da busca local.

## Experimentos (1000 execuções por algoritmo)

| Algoritmo | Melhor | Média | Desvio | Atingiu o ótimo | Tempo médio |
|---|---|---|---|---|---|
| Simulated Annealing | 1484.675006 | 1484.675006 | 0.000000 | 1000/1000 | 0.265 s |
| Hill Climbing (1 subida) | 1484.675006 | 1484.675006 | 0.000000 | 1000/1000 | 0.009 s |
| Hill Climbing (20 reinícios) | 1484.675006 | 1484.675006 | 0.000000 | 1000/1000 | 0.178 s |