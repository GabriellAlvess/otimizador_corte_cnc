# Otimizador de Corte 2D com Algoritmo Genético e Heurística Skyline
## Descrição

Este projeto implementa um sistema de otimização de corte 2D para máquinas CNC, utilizando algoritmos genéticos e heurísticas para encontrar o posicionamento ideal de peças em uma chapa, minimizando o desperdício de material.

## Funcionalidades

-- **Algoritmo Genético com Heurística Skyline** - Otimiza a disposição das peças na chapa
-- **Suporte a Múltiplos Formatos de Peças** - Retangular, circular, triangular e diamante
-- **Rotação Automática** - Testa rotações de 0° e 90° para otimizar o encaixe
-- **Visualização** - Apresenta layouts inicial e otimizado usando Matplotlib
-- **Cache de Fitness** - Melhora o desempenho evitando recálculos

## Estrutura do Projeto
```
otimizador_corte_cnc/
├── app.py                    # Arquivo principal da aplicação
├── genetic_algorithm.py      # Implementação do algoritmo genético
├── common/
│   └── layout_display.py     # Código para visualização dos layouts
└── __pycache__/              # Arquivos de cache Python
```

## Requisitos
- Python 3.x
- matplotlib
- numpy

## Instalação

```
# Clone o repositório
git clone https://github.com/seu-usuario/otimizador_corte_cnc.git

# Entre no diretório
cd otimizador_corte_cnc

# Instale as dependências
pip install matplotlib numpy

```
## Como Usar

Executando o programa
```
python app.py
```
## Configurando seu problema de corte
  Edite o arquivo ```app.py``` para definir:

1. As dimensões da chapa:
```
sheet_width = 200
sheet_height = 100
```

2. As peças a serem cortadas:
```
recortes_disponiveis = [
    {"tipo": "retangular", "largura": 29, "altura": 29, "x": 1, "y": 1},
    {"tipo": "circular", "r": 16, "x": 124, "y": 2},
    {"tipo": "diamante", "largura": 29, "altura": 48, "x": 32, "y": 31}
]
```
3. Parâmetros do algoritmo genético:
```
ga_optimizer = GeneticAlgorithm(TAM_POP=50, 
                               recortes_disponiveis=recortes_disponiveis,
                               sheet_width=sheet_width, 
                               sheet_height=sheet_height, 
                               numero_geracoes=100)
```
## Como Funciona

### Algoritmo Genético
O algoritmo genético implementado em ```genetic_algorithm.py``` funciona da seguinte forma:

1. **Inicialização:** Cria uma população de permutações aleatórias das peças
2. **Avaliação:** Calcula o fitness de cada permutação usando a heurística Skyline
3. **Seleção:** Usa seleção por torneio para escolher indivíduos para reprodução
4. **Cruzamento:** Aplica crossover de dois pontos para gerar novos indivíduos
5. **Mutação:** Introduz pequenas variações nos indivíduos com probabilidade mutation_rate
6. **Elitismo:** Preserva o melhor indivíduo entre gerações
7. **Reinicialização parcial:** A cada 10 gerações, parte da população é reinicializada

## Heurística Skyline
A heurística Skyline é usada para posicionar as peças na chapa:

1. Mantém um "horizonte" representando a altura ocupada em cada posição horizontal
2. Para cada peça, encontra a posição mais baixa possível no horizonte
3. Atualiza o horizonte após colocar cada peça
4. Tenta diferentes rotações para peças retangulares e diamante













