import random
import copy
from typing import List, Dict, Any, Tuple
from common.layout_display import LayoutDisplayMixin


class GeneticAlgorithm(LayoutDisplayMixin):
    def __init__(
        self,
        TAM_POP: int,
        recortes_disponiveis: List[Dict[str, Any]],
        sheet_width: float,
        sheet_height: float,
        numero_geracoes: int = 100
    ):
        """
        Inicializa o algoritmo genético com os parâmetros fornecidos.
        - TAM_POP: Tamanho da população.
        - recortes_disponiveis: Lista de peças disponíveis para corte.
        - sheet_width: Largura da chapa.
        - sheet_height: Altura da chapa.
        - numero_geracoes: Número de gerações que o algoritmo irá executar.
        """
        print("GA 2D Skyline Heuristic - Sem redimensionar, sem multi-chapas, bounding box fixo.")
        self.TAM_POP = TAM_POP
        self.recortes_disponiveis = recortes_disponiveis
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.numero_geracoes = numero_geracoes

        # População: cada indivíduo é uma permutação das peças
        self.POP: List[List[int]] = []
        self.best_individual: List[int] = []  # Melhor indivíduo encontrado
        self.best_layout: List[Dict[str, Any]] = []  # Melhor layout encontrado
        self.best_fitness: float = float('inf')  # Melhor fitness (quanto menor, melhor)
        self.optimized_layout = None  # Layout otimizado final

        # Parâmetros do algoritmo genético
        self.mutation_rate = 0.1  # Taxa de mutação
        self.elitism = True  # Preserva o melhor indivíduo entre gerações

        # Cache de fitness e lista de fitness da população
        self.fitness_cache = {}  # Armazena fitness já calculados para evitar recálculos
        self.population_fitness = []  # Armazena o fitness de cada indivíduo da população atual

        self.initialize_population()  # Inicializa a população

    def initialize_population(self):
        """
        Inicializa a população com permutações aleatórias das peças.
        Cada indivíduo é uma lista de índices que representa uma ordem de colocação das peças.
        """
        n = len(self.recortes_disponiveis)
        base = list(range(n))
        for _ in range(self.TAM_POP):
            perm = base[:]
            random.shuffle(perm)
            self.POP.append(perm)

    def get_dims(self, rec: Dict[str, Any], rot: int) -> Tuple[float, float]:
        """
        Retorna as dimensões (largura, altura) de uma peça, considerando sua rotação.
        - rec: Dicionário que descreve a peça.
        - rot: Rotação da peça (0° ou 90°).
        """
        tipo = rec["tipo"]
        if tipo == "circular":
            d = 2 * rec["r"]
            return (d, d)
        elif tipo in ("retangular", "diamante"):
            if rot == 90:
                return (rec["altura"], rec["largura"])
            else:
                return (rec["largura"], rec["altura"])
        else:
            return (rec.get("largura", 10), rec.get("altura", 10))

    def decode_layout(self, permutation: List[int]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Decodifica uma permutação em um layout usando a heurística Skyline.
        - permutation: Lista de índices que representa a ordem de colocação das peças.
        Retorna:
        - layout_result: Lista de peças posicionadas no layout.
        - discarded: Número de peças que não couberam na chapa.
        """
        layout_result: List[Dict[str, Any]] = []
        skyline = [0.0] * int(self.sheet_width)  # Inicializa o skyline com altura zero
        discarded = 0  # Contador de peças descartadas

        for idx in permutation:
            rec = self.recortes_disponiveis[idx]
            possible_configs = []
            if rec["tipo"] in ("retangular", "diamante"):
                for rot in [0, 90]:  # Tenta rotações 0° e 90°
                    w, h = self.get_dims(rec, rot)
                    possible_configs.append((rot, w, h))
            else:
                w, h = self.get_dims(rec, 0)
                possible_configs.append((0, w, h))

            placed = False
            for (rot, w, h) in possible_configs:
                best_x, best_y = self.find_best_position(skyline, w, h)
                if best_x != -1:  # Se a peça couber no skyline
                    placed = True
                    r_final = copy.deepcopy(rec)
                    r_final["rotacao"] = rot
                    r_final["x"] = best_x
                    r_final["y"] = best_y
                    layout_result.append(r_final)
                    self.update_skyline(skyline, best_x, best_y, w, h)  # Atualiza o skyline
                    break
            if not placed:
                discarded += 1  # Peça descartada se não couber

        return (layout_result, discarded)

    def find_best_position(self, skyline: List[float], w: float, h: float) -> Tuple[int, float]:
        """
        Encontra a posição mais baixa no skyline onde a peça cabe.
        - skyline: Lista que armazena a altura acumulada em cada posição horizontal.
        - w: Largura da peça.
        - h: Altura da peça.
        Retorna:
        - best_x: Posição horizontal onde a peça será colocada.
        - best_y: Altura onde a peça será colocada.
        """
        best_x = -1
        best_y = float('inf')
        w_int = int(w)
        max_pos = len(skyline) - w_int + 1

        for x in range(max_pos):
            max_height = 0
            for i in range(w_int):
                if skyline[x + i] > max_height:
                    max_height = skyline[x + i]
            if max_height + h <= self.sheet_height and max_height < best_y:
                best_x = x
                best_y = max_height
        return (best_x, best_y)

    def update_skyline(self, skyline: List[float], x: int, y: float, w: float, h: float):
        """
        Atualiza o skyline após colocar uma peça.
        - skyline: Lista que armazena a altura acumulada em cada posição horizontal.
        - x: Posição horizontal onde a peça foi colocada.
        - y: Altura onde a peça foi colocada.
        - w: Largura da peça.
        - h: Altura da peça.
        """
        for i in range(x, x + int(w)):
            skyline[i] = y + h

    def evaluate_individual(self, permutation: List[int]) -> float:
        """
        Avalia um indivíduo (permutação) e retorna seu fitness.
        - permutation: Lista de índices que representa a ordem de colocação das peças.
        Retorna:
        - fitness: Valor que representa a qualidade do indivíduo (quanto menor, melhor).
        """
        perm_key = tuple(permutation)
        if perm_key in self.fitness_cache:  # Usa cache para evitar recálculos
            return self.fitness_cache[perm_key]

        layout, discarded = self.decode_layout(permutation)

        if not layout:  # Se nenhuma peça foi colocada
            fitness = self.sheet_width * self.sheet_height * 2 + discarded * 10000
            self.fitness_cache[perm_key] = fitness
            return fitness

        # Calcula o bounding box do layout
        x_min, x_max = float('inf'), float('-inf')
        y_min, y_max = float('inf'), float('-inf')

        for rec in layout:
            angle = rec.get("rotacao", 0)
            w, h = self.get_dims(rec, angle)
            x0, y0 = rec["x"], rec["y"]
            x1, y1 = x0 + w, y0 + h
            x_min = min(x_min, x0)
            x_max = max(x_max, x1)
            y_min = min(y_min, y0)
            y_max = max(y_max, y1)

        area_layout = (x_max - x_min) * (y_max - y_min)
        penalty = discarded * 10000  # Penalidade por peças descartadas
        fitness = area_layout + penalty
        self.fitness_cache[perm_key] = fitness
        return fitness

    def evaluate_population(self):
        """
        Avalia todos os indivíduos da população e armazena seus fitness.
        Atualiza o melhor indivíduo e o melhor fitness encontrado.
        """
        self.population_fitness = []
        for perm in self.POP:
            fit = self.evaluate_individual(perm)
            self.population_fitness.append(fit)
            if fit < self.best_fitness:  # Atualiza o melhor indivíduo
                self.best_fitness = fit
                self.best_individual = perm[:]

    def compute_fitness_scores(self) -> List[float]:
        """
        Converte os fitness em scores para seleção.
        Retorna uma lista de scores, onde scores maiores indicam indivíduos melhores.
        """
        return [1 / (1 + f) for f in self.population_fitness]

    def tournament_selection(self, tournament_size=3) -> List[int]:
        """
        Seleção por torneio: escolhe o melhor entre `tournament_size` indivíduos aleatórios.
        - tournament_size: Número de indivíduos no torneio.
        Retorna o melhor indivíduo do torneio.
        """
        indices = random.sample(range(len(self.POP)), tournament_size)
        best_idx = min(indices, key=lambda i: self.population_fitness[i])
        return self.POP[best_idx]

    def crossover_two_point(self, p1: List[int], p2: List[int]) -> List[int]:
        """
        Crossover de dois pontos: combina partes de dois pais para gerar um filho.
        - p1: Primeiro pai.
        - p2: Segundo pai.
        Retorna um filho gerado a partir dos pais.
        """
        size = len(p1)
        i1, i2 = sorted(random.sample(range(size), 2))
        child = [None] * size
        child[i1:i2 + 1] = p1[i1:i2 + 1]
        p2_idx = 0
        for i in range(size):
            if child[i] is None:
                while p2[p2_idx] in child:
                    p2_idx += 1
                child[i] = p2[p2_idx]
                p2_idx += 1
        return child

    def mutate(self, perm: List[int]) -> List[int]:
        """
        Mutação: troca duas posições aleatórias com probabilidade `mutation_rate`.
        - perm: Indivíduo a ser mutado.
        Retorna o indivíduo mutado.
        """
        if random.random() < self.mutation_rate:
            i1, i2 = random.sample(range(len(perm)), 2)
            perm[i1], perm[i2] = perm[i2], perm[i1]
        return perm

    def genetic_operators(self):
        """
        Aplica os operadores genéticos (seleção, crossover e mutação) para gerar uma nova população.
        Preserva o melhor indivíduo se elitismo estiver ativado.
        """
        new_pop = []
        if self.elitism and self.best_individual:  # Preserva o melhor indivíduo
            new_pop.append(self.best_individual[:])
        while len(new_pop) < self.TAM_POP:
            p1 = self.tournament_selection()
            p2 = self.tournament_selection()
            child = self.crossover_two_point(p1, p2)
            child = self.mutate(child)
            new_pop.append(child)
        self.POP = new_pop[:self.TAM_POP]

    def run(self):
        """
        Executa o algoritmo genético por `numero_geracoes` gerações.
        Retorna o layout otimizado.
        """
        for gen in range(self.numero_geracoes):
            self.evaluate_population()
            self.genetic_operators()
            if gen % 10 == 0:
                print(f"Geração {gen} - Melhor Fitness: {self.best_fitness}")
        layout, discarded = self.decode_layout(self.best_individual)
        self.optimized_layout = layout
        return self.optimized_layout

    def optimize_and_display(self):
        """
        Exibe o layout inicial e o layout final otimizado.
        Retorna o layout otimizado.
        """
        self.display_layout(self.recortes_disponiveis, title="Initial Layout - GA")
        self.run()
        self.display_layout(self.optimized_layout, title="Optimized Layout - GA")
        return self.optimized_layout