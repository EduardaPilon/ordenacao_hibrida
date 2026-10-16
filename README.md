# A ordenação híbrida: rápida + inserção

Estudo do ponto de troca entre a ordenação rápida (*quicksort*) e a ordenação
por inserção (*insertion sort*). A ideia é usar a rápida nos pedaços grandes,
onde ela é eficiente, e entregar os pedaços pequenos para a inserção, que tem
custo por comparação muito baixo. O limiar que decide essa troca é o parâmetro
`corte`.

## Objetivo

1. Implementar a ordenação rápida com pivô aleatório e partição de três vias
   (menores, iguais, maiores).
2. Transformá-la em híbrida: chamar a inserção quando o pedaço tiver menos que
   `corte` elementos, sendo `corte` um parâmetro da função.
3. Medir o tempo com 20 mil elementos aleatórios variando o corte em
   `1, 5, 10, 16, 20, 32, 50, 100, 200`.
4. Comparar com a ordenação rápida pura e descobrir o melhor corte.

## Estrutura do projeto

```
.
├── src/
│   ├── ordenacoes.py     # inserção, quicksort puro e quicksort híbrido
│   └── benchmark.py      # experimento: mede, compara e gera os artefatos
├── tests/
│   ├── test_ordenacoes.py     # testes de correção (stdlib apenas)
│   └── validar_artefatos.py   # confere tabela, CSV, gráfico e o relatório
├── resultados/
│   ├── tempos.csv        # dados brutos
│   ├── tabela.md         # tabela em Markdown
│   └── tempo_vs_corte.png  # gráfico tempo × corte
└── RELATORIO.md          # este relatório
```

## Como reproduzir

Requer apenas Python 3.10+ e `matplotlib` (único pacote externo).

```bash
python3 -m tests.test_ordenacoes     # testes de correção (9 testes)
python3 -m src.benchmark             # roda o experimento e gera resultados/
python3 -m tests.validar_artefatos   # confere os resultados contra o relatório
```

Os resultados deste relatório foram produzidos pelo segundo comando.
