from common.layout_display import LayoutDisplayMixin
import random
import copy
import math

class GeneticAlgorithm(LayoutDisplayMixin):
    def __init__(self, TAM_POP, recortes_disponiveis, sheet_width, sheet_height, numero_geracoes=100):
        self.TAM_POP = TAM_POP
        self.initial_layout = recortes_disponiveis
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.numero_geracoes = numero_geracoes
        
        self.POP = []
        self.POP_AUX = []
        self.aptidao = []
        self.melhor_aptidoes = []
        self.optimized_layout = None

        # Parâmetros do AG
        self.taxa_crossover = 0.8
        self.taxa_mutacao = 0.1
        self.p_torneio = 0.75  # probabilidade de pegar o melhor no torneio

        # Inicializar população
        self.initialize_population()

    def initialize_population(self):
        """
        Inicializa a população de indivíduos.
        Cada indivíduo é uma lista da forma:
        [
          {"indice_peca": i, "rotacao": 0 ou 90 ou 180 ou 270},
          ...
        ]
        """
        self.POP = []
        for _ in range(self.TAM_POP):
            individuo = []
            for i, recorte in enumerate(self.initial_layout):
                rotacao = random.choice([0, 90, 180, 270]) if "rotacao" in recorte else 0
                individuo.append({"indice_peca": i, "rotacao": rotacao})
            random.shuffle(individuo)
            self.POP.append(individuo)
        self.evaluate()

    def evaluate(self):
        """
        Avalia cada indivíduo usando:
        - Skyline para posicionar
        - cálculo de fitness com múltiplos fatores (utilização, compactação, penalizações)
        """
        self.aptidao = []
        
        for individuo in self.POP:
            layout_atual = self._aplicar_skyline(individuo)
            area_total = self.sheet_width * self.sheet_height
            area_utilizada = self._calcular_area_utilizada(layout_atual)
            altura_maxima = self._calcular_altura_maxima(layout_atual)
            
            # Critérios
            compactacao = 1.0 - (altura_maxima / self.sheet_height)
            utilizacao = area_utilizada / area_total
            
            sobreposicoes = self._verificar_sobreposicoes(layout_atual)
            fora_limites = self._verificar_limites(layout_atual)
            
            # Exemplo de fitness mais avançado:
            # Tentar equilibrar uso de área e compactação, penalizando sobreposição e fora dos limites
            fitness = (0.5 * utilizacao + 0.5 * compactacao)
            fitness *= (1.0 - 0.5 * sobreposicoes)
            fitness *= (1.0 - 0.5 * fora_limites)
            
            self.aptidao.append(fitness)

    def _aplicar_skyline(self, individuo):
        """
        Aplica a heurística Skyline mantendo o tipo original das peças.
        """
        skyline = [(0, 0), (self.sheet_width, 0)]
        layout_resultante = []

        for gene in individuo:
            # Copia a peça original mantendo TODOS os atributos
            peca = copy.deepcopy(self.initial_layout[gene["indice_peca"]])

            # Apenas atualiza a rotação se a peça permitir
            if "rotacao" in peca:
                peca["rotacao"] = gene["rotacao"]

            # Encontra a melhor posição mantendo o tipo original
            x, y = self._encontrar_melhor_posicao_skyline(skyline, peca)
            peca["x"] = x
            peca["y"] = y

            # Atualiza o skyline considerando as dimensões corretas da peça
            self._atualizar_skyline(skyline, peca)
            layout_resultante.append(peca)

        return layout_resultante
    
    def _obter_largura(self, peca):
        """
        Retorna a largura efetiva da peça usando o campo auxiliar se existir.
        """
        return peca.get("pos_largura", peca.get("largura", peca.get("r", 0) * 2 if peca["tipo"] == "circular" else peca.get("b", 0)))
    
    def _obter_altura(self, peca):
        """
        Retorna a altura efetiva da peça usando o campo auxiliar se existir.
        """
        return peca.get("pos_altura", peca.get("altura", peca.get("r", 0) * 2 if peca["tipo"] == "circular" else peca.get("h", 0)))

    def _encontrar_melhor_posicao_skyline(self, skyline, peca):
        """
        Tenta colocar a peça em cada segmento possível do skyline e escolhe a posição
        que minimize desperdício ou maximize aproveitamento.
        """
        largura = self._obter_largura(peca)
        altura = self._obter_altura(peca)
        melhor_x, melhor_y = 0, float('inf')
        melhor_peso = float('inf')
        
        if largura > self.sheet_width:
            return 0, 0  # Não cabe
        
        for i in range(len(skyline) - 1):
            x_atual = skyline[i][0]
            y_atual = skyline[i][1]
            if x_atual + largura <= self.sheet_width:
                # Altura skyline no intervalo
                y_altura = max(y_atual, skyline[i+1][1])
                if y_altura + altura <= self.sheet_height:
                    # Avaliar "peso" (ex.: quão alto começa)
                    # Quanto menor y_altura, melhor
                    peso = y_altura
                    if peso < melhor_peso:
                        melhor_peso = peso
                        melhor_x, melhor_y = x_atual, y_altura
        # Se não achou, coloca no menor y do skyline
        if melhor_peso == float('inf'):
            min_altura = min(seg[1] for seg in skyline)
            melhor_x, melhor_y = 0, min_altura
        return melhor_x, melhor_y

    def _atualizar_skyline(self, skyline, peca):
        """
        Atualiza os segmentos do skyline após colocar a peça.
        """
        x, y = peca["x"], peca["y"]
        larg = self._obter_largura(peca)
        alt = self._obter_altura(peca)
        nova_altura = y + alt
        
        # Remover trechos que estão cobertos
        i = 0
        while i < len(skyline):
            if x <= skyline[i][0] < x + larg:
                skyline.pop(i)
            else:
                i += 1
        # Inserir pontos de bordo da peça
        skyline.append((x, nova_altura))
        skyline.append((x+larg, y))
        skyline.sort(key=lambda s: s[0])
        # Consolidar
        i = 0
        while i < len(skyline)-1:
            if skyline[i][1] == skyline[i+1][1]:
                skyline.pop(i+1)
            else:
                i += 1

    def _obter_largura(self, peca):
        if peca["tipo"] == "circular":
            return 2*peca["r"]
        elif peca["tipo"] == "triangular":
            return peca["b"]
        else:  # retangular ou diamante
            return peca["largura"]

    def _obter_altura(self, peca):
        if peca["tipo"] == "circular":
            return 2*peca["r"]
        elif peca["tipo"] == "triangular":
            return peca["h"]
        else:  # retangular ou diamante
            return peca["altura"]

    def _calcular_area_utilizada(self, layout):
        area_total = 0
        for peca in layout:
            if peca["tipo"] == "circular":
                area_total += math.pi * peca["r"]**2
            elif peca["tipo"] == "triangular":
                area_total += 0.5 * peca["b"] * peca["h"]
            elif peca["tipo"] == "diamante":
                area_total += 0.5 * peca["largura"] * peca["altura"]
            else:
                area_total += peca["largura"] * peca["altura"]
        return area_total

    def _calcular_altura_maxima(self, layout):
        altura = 0
        for p in layout:
            if p["tipo"]=="circular":
                altura = max(altura, p["y"] + 2*p["r"])
            elif p["tipo"]=="triangular":
                altura = max(altura, p["y"] + p["h"])
            else:
                altura = max(altura, p["y"] + p["altura"])
        return altura
    
    def _verificar_sobreposicoes(self, layout):
        total = 0
        n = len(layout)
        for i in range(n):
            for j in range(i+1,n):
                box1 = self._bbox(layout[i])
                box2 = self._bbox(layout[j])
                if (box1[0]<box2[2] and box1[2]>box2[0] and
                    box1[1]<box2[3] and box1[3]>box2[1]):
                    total += 1
        max_pares = n*(n-1)/2
        return total/max_pares if max_pares>0 else 0

    def _bbox(self, p):
        if p["tipo"]=="circular":
            return (p["x"], p["y"], p["x"]+2*p["r"], p["y"]+2*p["r"])
        elif p["tipo"]=="triangular":
            return (p["x"], p["y"], p["x"]+p["b"], p["y"]+p["h"])
        else:
            return (p["x"], p["y"], p["x"]+p["largura"], p["y"]+p["altura"])

    def _verificar_limites(self, layout):
        count_fora = 0
        for p in layout:
            box = self._bbox(p)
            if (box[0]<0 or box[1]<0 or box[2]>self.sheet_width or box[3]>self.sheet_height):
                count_fora += 1
        return count_fora/len(layout) if layout else 0

    def genetic_operators(self):
        """
        Operadores Genéticos mais avançados:
        - Elitismo
        - Seleção por torneio com probabilidade p_torneio
        - Crossover (PMX)
        - Mutação com troca múltipla e rotação
        """
        self.POP_AUX = []
        best_idx = max(range(self.TAM_POP), key=lambda i: self.aptidao[i])
        self.POP_AUX.append(copy.deepcopy(self.POP[best_idx]))
        
        while len(self.POP_AUX)<self.TAM_POP:
            p1 = self._selecao_torneio()
            p2 = self._selecao_torneio()
            parent1 = self.POP[p1]
            parent2 = self.POP[p2]

            if random.random() < self.taxa_crossover:
                f1, f2 = self._crossover_ordenamento(parent1, parent2)
            else:
                f1, f2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
            
            self._mutacao(f1)
            self._mutacao(f2)
            
            self.POP_AUX.append(f1)
            if len(self.POP_AUX)<self.TAM_POP:
                self.POP_AUX.append(f2)

        self.POP = copy.deepcopy(self.POP_AUX)

    def _selecao_torneio(self, tam=3):
        competidores = random.sample(range(self.TAM_POP), tam)
        competidores.sort(key=lambda i: self.aptidao[i], reverse=True)
        # Com probabilidade p_torneio pega o melhor, caso contrário pega outro
        if random.random()<self.p_torneio:
            return competidores[0]
        else:
            return random.choice(competidores[1:])

    def _crossover_ordenamento(self, pai1, pai2):
        """
        PMX - Partially Mapped Crossover com detecção de ciclos.
        Mantém os atributos originais das peças, apenas alterando a ordem e a rotação.
        """
        n = len(pai1)
        c1, c2 = [None] * n, [None] * n
        p1 = random.randint(0, n - 2)
        p2 = random.randint(p1 + 1, n - 1)

        # Copiar a parte central dos pais para os filhos
        for i in range(p1, p2 + 1):
            c1[i] = {"indice_peca": pai1[i]["indice_peca"], "rotacao": pai1[i]["rotacao"]}
            c2[i] = {"indice_peca": pai2[i]["indice_peca"], "rotacao": pai2[i]["rotacao"]}

        # Criar os mapeamentos
        map1, map2 = {}, {}
        for i in range(p1, p2 + 1):
            map1[pai1[i]["indice_peca"]] = pai2[i]["indice_peca"]
            map2[pai2[i]["indice_peca"]] = pai1[i]["indice_peca"]

        for i in range(n):
            if i < p1 or i > p2:
                # Preencher filho 1
                gene1 = pai2[i]["indice_peca"]
                visited = set()
                while gene1 in map2:
                    if gene1 in visited:
                        break
                    visited.add(gene1)
                    gene1 = map2[gene1]
                c1[i] = {"indice_peca": gene1, "rotacao": pai2[i]["rotacao"]}

                # Preencher filho 2
                gene2 = pai1[i]["indice_peca"]
                visited = set()
                while gene2 in map1:
                    if gene2 in visited:
                        break
                    visited.add(gene2)
                    gene2 = map1[gene2]
                c2[i] = {"indice_peca": gene2, "rotacao": pai1[i]["rotacao"]}

        return c1, c2

    def _mutacao(self, individuo):
        """
        - Troca múltipla de posições
        - Rotação aleatória
        - Mantém os atributos originais das peças.
        """
        # Várias trocas
        if random.random() < self.taxa_mutacao * 2:
            n_trocas = random.randint(1, max(1, int(len(individuo) * 0.2)))
            for _ in range(n_trocas):
                i1, i2 = random.sample(range(len(individuo)), 2)
                individuo[i1], individuo[i2] = individuo[i2], individuo[i1]
        # Rotações aleatórias
        for g in individuo:
            if random.random() < self.taxa_mutacao * 1.5:
                g["rotacao"] = random.choice([0, 90, 180, 270])

    def run(self):
        melhor_global = None
        melhor_aptidao_global = -float("inf")
        print("\n=== Iniciando Otimização por Algoritmo Genético (Complexo) ===")
        print(f"População: {self.TAM_POP} | Gerações: {self.numero_geracoes}")
        
        print("Avaliando população inicial...")
        self.evaluate()
        if self.aptidao:
            idx_best = self.aptidao.index(max(self.aptidao))
            melhor_aptidao_global = self.aptidao[idx_best]
            melhor_global = copy.deepcopy(self.POP[idx_best])
            print(f"Fitness inicial: {melhor_aptidao_global:.4f}")

        print("\nEvolução...")
        for gen in range(self.numero_geracoes):
            # Operadores genéticos
            self.genetic_operators()
            # Avaliação
            self.evaluate()
            # Melhor da geração
            idx_best = self.aptidao.index(max(self.aptidao))
            if self.aptidao[idx_best]>melhor_aptidao_global:
                melhor_aptidao_global = self.aptidao[idx_best]
                melhor_global = copy.deepcopy(self.POP[idx_best])
                print(f"Geração {gen+1}/{self.numero_geracoes} - Novo Melhor: {melhor_aptidao_global:.4f}")
            else:
                print(f"Geração {gen+1}/{self.numero_geracoes} - Melhor Atual: {melhor_aptidao_global:.4f}")

        print("\n=== Concluído! Melhor aptidão: {:.4f} ===".format(melhor_aptidao_global))
        self.optimized_layout = self._aplicar_skyline(melhor_global)
        return self.optimized_layout

    def optimize_and_display(self):
        self.display_layout(self.initial_layout, title="Layout Inicial")
        self.optimized_layout = self.run()
        self.display_layout(self.optimized_layout, title="Layout Otimizado")
        return self.optimized_layout