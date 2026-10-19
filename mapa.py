import config
from typing import List


class Mapa:
    def __init__(self, caminho_arquivo=config.ARQUIVO_MAPA):
        self.grid = self._ler_arquivo(caminho_arquivo)
        self.linhas = len(self.grid)
        self.colunas = len(self.grid[0])

        self.origem = None
        self.destino = None
        self.ginasios = {}
        self._localizar_pontos()

        self.posicoes_ginasios = set(self.ginasios.values())

    def _ler_arquivo(self, caminho_arquivo) -> List[str]:
        """Lê o arquivo texto e transforma em uma lista de strings representando o mapa.

        Args:
            caminho_arquivo: caminho do arquivo texto com o mapa.

        Returns:
            Lista com uma string por linha do mapa.

        Raises:
            ValueError: se o mapa não tiver config.LINHAS linhas ou se alguma
                linha não tiver config.COLUNAS colunas.
        """
        with open(caminho_arquivo, encoding="utf-8") as f:
            grid = [linha.rstrip("\n\r") for linha in f if linha.strip()]

        if len(grid) != config.LINHAS:
            raise ValueError(
                f"Mapa com {len(grid)} linhas; esperado {config.LINHAS}."
            )

        for i, linha in enumerate(grid):
            if len(linha) != config.COLUNAS:
                raise ValueError(
                    f"Linha {i} do mapa tem {len(linha)} colunas, esperado {config.COLUNAS}."
                )
        return grid

    def _localizar_pontos(self):
        """Percorre o mapa e guarda onde estão origem, destino e ginásios.

        Raises:
            ValueError: se aparecer um símbolo desconhecido ou se faltar a
                origem, o destino ou algum ginásio.
        """
        for l, linha in enumerate(self.grid):
            for c, simbolo in enumerate(linha):
                if simbolo == config.SIMBOLO_ORIGEM:
                    self.origem = (l, c)

                elif simbolo == config.SIMBOLO_DESTINO:
                    self.destino = (l, c)

                elif simbolo in config.DIFICULDADE:
                    self.ginasios[simbolo] = (l, c)

                elif simbolo not in config.CUSTO_TERRENO:
                    raise ValueError(
                        f"Símbolo desconhecido '{simbolo}' na posição ({l}, {c})."
                    )

        if self.origem is None:
            raise ValueError("Origem ('1') não encontrada no mapa.")

        if self.destino is None:
            raise ValueError("Destino ('U') não encontrado no mapa.")

        faltando = set(config.DIFICULDADE) - set(self.ginasios)
        if faltando:
            raise ValueError(f"Ginásios não encontrados no mapa: {sorted(faltando)}")

        self.ginasios = {g: self.ginasios[g] for g in config.DIFICULDADE}

    def dentro(self, l, c):
        """Diz se (l, c) está dentro dos limites do mapa.

        Args:
            l: linha.
            c: coluna.

        Returns:
            True se a posição está dentro do mapa.
        """
        return 0 <= l < self.linhas and 0 <= c < self.colunas

    def custo(self, l, c):
        """Custo (em minutos) para ENTRAR na célula (l, c).

        - Terrenos (M, A, F, R, .): valor de config.CUSTO_TERRENO.
        - Origem e destino: config.CUSTO_ORIGEM_DESTINO (+1).
        - Ginásios: config.CUSTO_GINASIO (0; só conta a batalha).

        Args:
            l: linha.
            c: coluna.

        Returns:
            Custo em minutos para entrar na célula.
        """
        simbolo = self.grid[l][c]
        if simbolo in config.CUSTO_TERRENO:
            return config.CUSTO_TERRENO[simbolo]

        if simbolo in (config.SIMBOLO_ORIGEM, config.SIMBOLO_DESTINO):
            return config.CUSTO_ORIGEM_DESTINO

        return config.CUSTO_GINASIO

    def vizinhos(self, l, c):
        """Células vizinhas de (l, c): cima, baixo, esquerda e direita.

        Não há movimento na diagonal. Só devolve posições dentro do mapa.

        Args:
            l: linha.
            c: coluna.

        Yields:
            Tuplas (linha, coluna) de cada vizinho.
        """
        for dl, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nl, nc = l + dl, c + dc
            if self.dentro(nl, nc):
                yield nl, nc