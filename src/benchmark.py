"""Mede o tempo da ordenação híbrida variando o corte e compara com a rápida pura.

Uso (a partir da raiz do projeto):

    python3 -m src.benchmark

Gera, em ``resultados/``:

* ``tempos.csv``            -- dados brutos (tempo médio, desvio, mínimo);
* ``tabela.md``             -- a mesma tabela em Markdown, pronta para o relatório;
* ``tempo_vs_corte.png``    -- gráfico do tempo em função do corte.
"""

from __future__ import annotations

import csv
import random
import statistics
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sem janela, só para salvar o arquivo
import matplotlib.pyplot as plt

from src.ordenacoes import quicksort_hibrido, quicksort_puro

# ---------------------------------------------------------------------------
# Parâmetros do experimento
# ---------------------------------------------------------------------------
N = 20_000                                  # tamanho do vetor
CORTES = [1, 5, 10, 16, 20, 32, 50, 100, 200]
REPETICOES = 25                             # execuções por configuração
SEMENTE_DADOS = 2024                        # geracao dos vetores aleatorios
SEMENTE_PIVO = 7                            # sorteio dos pivôs (igual para todos)

RAIZ = Path(__file__).resolve().parent.parent
PASTA_RESULTADOS = RAIZ / "resultados"


def gerar_vetor(n: int, semente: int) -> list[int]:
    """Vetor de ``n`` inteiros aleatórios (repetições são possíveis)."""
    gerador = random.Random(semente)  # criado uma única vez por vetor
    return [gerador.randint(0, 10 * n) for _ in range(n)]


def cronometrar(funcao, dados: list[int], rng: random.Random) -> float:
    """Tempo, em milissegundos, de uma execução sobre uma cópia de ``dados``."""
    copia = list(dados)
    inicio = time.perf_counter()
    funcao(copia, rng)
    fim = time.perf_counter()
    if copia != sorted(dados):  # salvaguarda: resultado tem de estar ordenado
        raise AssertionError("resultado incorreto")
    return (fim - inicio) * 1000.0


def medir(configs: list[tuple[str, object]], vetores: list[list[int]]) -> list[dict]:
    """Mede todas as configurações em rodadas intercaladas.

    Cada rodada aplica todas as configurações ao *mesmo* vetor, em ordem
    rotacionada. Assim, variações lentas do ambiente (aquecimento da CPU,
    coletor de lixo, realocação de memória) atingem todas igualmente, em vez
    de penalizar a primeira configuração medida.
    """
    tempos: dict[str, list[float]] = {rotulo: [] for rotulo, _ in configs}

    # Aquecimento: tira o processo do estado "frio" antes de medir a sério.
    for _ in range(3):
        for _, funcao in configs:
            cronometrar(funcao, vetores[0], random.Random(SEMENTE_PIVO))

    for rep, vetor in enumerate(vetores):
        deslocamento = rep % len(configs)
        ordem = configs[deslocamento:] + configs[:deslocamento]
        for rotulo, funcao in ordem:
            tempos[rotulo].append(cronometrar(funcao, vetor, random.Random(SEMENTE_PIVO)))

    linhas = [
        {
            "configuracao": rotulo,
            "tempo_medio_ms": statistics.fmean(tempos[rotulo]),
            "desvio_ms": statistics.stdev(tempos[rotulo]),
            "tempo_minimo_ms": min(tempos[rotulo]),
        }
        for rotulo, _ in configs
    ]

    base = linhas[0]["tempo_medio_ms"]
    for linha in linhas:
        linha["ganho_vs_pura_%"] = (base - linha["tempo_medio_ms"]) / base * 100.0
    return linhas


def main() -> None:
    PASTA_RESULTADOS.mkdir(exist_ok=True)

    # Todos os algoritmos ordenam exatamente os mesmos vetores, para a
    # comparação ser justa (o trabalho depende da entrada, não da sorte).
    vetores = [gerar_vetor(N, SEMENTE_DADOS + r) for r in range(REPETICOES)]

    # Salvaguarda contra entradas degeneradas (vetor constante já sai ordenado
    # da partição de três vias e mediria um tempo irreal).
    if len(set(vetores[0])) < N // 2:
        raise AssertionError("os vetores de teste não são suficientemente aleatórios")

    configs: list[tuple[str, object]] = [("pura", lambda v, r: quicksort_puro(v, r))]
    for corte in CORTES:
        configs.append(
            (f"hibrida {corte}", lambda v, r, c=corte: quicksort_hibrido(v, c, r))
        )

    linhas = medir(configs, vetores)

    escrever_csv(linhas)
    escrever_markdown(linhas)
    gerar_grafico(linhas)
    imprimir_resumo(linhas)


def escrever_csv(linhas: list[dict]) -> None:
    caminho = PASTA_RESULTADOS / "tempos.csv"
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({k: formatar(v) for k, v in linha.items()})


def formatar(valor):
    return f"{valor:.3f}" if isinstance(valor, float) else valor


def escrever_markdown(linhas: list[dict]) -> None:
    caminho = PASTA_RESULTADOS / "tabela.md"
    cabecalho = (
        "| Configuração | Tempo médio (ms) | Desvio padrão (ms) | Mínimo (ms) | "
        "Ganho vs. pura (%) |\n"
        "| --- | ---: | ---: | ---: | ---: |\n"
    )
    corpo = "".join(
        f"| {linha['configuracao']} | {linha['tempo_medio_ms']:.2f} | "
        f"{linha['desvio_ms']:.2f} | {linha['tempo_minimo_ms']:.2f} | "
        f"{linha['ganho_vs_pura_%']:+.1f} |\n"
        for linha in linhas
    )
    caminho.write_text(cabecalho + corpo, encoding="utf-8")


def gerar_grafico(linhas: list[dict]) -> None:
    hibridas = linhas[1:]
    tempos = [l["tempo_medio_ms"] for l in hibridas]
    erros = [l["desvio_ms"] for l in hibridas]
    base = linhas[0]["tempo_medio_ms"]
    melhor = min(hibridas, key=lambda l: l["tempo_medio_ms"])

    figura, eixo = plt.subplots(figsize=(9, 5))
    eixo.errorbar(CORTES, tempos, yerr=erros, marker="o", capsize=3,
                  color="#1f4e79", label="híbrida (rápida + inserção)")
    eixo.axhline(base, linestyle="--", color="#c00000",
                 label=f"rápida pura ({base:.1f} ms)")
    eixo.axvline(int(melhor["configuracao"].split()[1]), linestyle=":", color="#548235")
    eixo.annotate(
        f"melhor corte = {melhor['configuracao'].split()[1]}\n{melhor['tempo_medio_ms']:.1f} ms",
        xy=(int(melhor["configuracao"].split()[1]), melhor["tempo_medio_ms"]),
        xytext=(12, 14), textcoords="offset points", color="#548235", fontsize=9,
    )

    eixo.set_xscale("log")
    eixo.set_xticks(CORTES)
    eixo.set_xticklabels(CORTES)
    eixo.set_xlabel("Corte (nº mínimo de elementos para usar a rápida)")
    eixo.set_ylabel("Tempo médio (ms)")
    eixo.set_title(f"Tempo da ordenação híbrida em função do corte\n{N:,} elementos aleatórios, média de {REPETICOES} execuções".replace(",", "."))
    eixo.grid(True, which="both", alpha=0.3)
    eixo.legend()
    figura.tight_layout()

    caminho = PASTA_RESULTADOS / "tempo_vs_corte.png"
    figura.savefig(caminho, dpi=150)
    plt.close(figura)


def imprimir_resumo(linhas: list[dict]) -> None:
    base = linhas[0]
    hibridas = linhas[1:]
    melhor = min(hibridas, key=lambda l: l["tempo_medio_ms"])
    pior = max(hibridas, key=lambda l: l["tempo_medio_ms"])

    print(f"N = {N} elementos aleatorios, {REPETICOES} repeticoes por configuracao\n")
    print(f"{'configuracao':<14}{'media (ms)':>12}{'desvio':>10}{'minimo':>10}{'ganho %':>10}")
    for linha in linhas:
        print(
            f"{linha['configuracao']:<14}{linha['tempo_medio_ms']:>12.2f}"
            f"{linha['desvio_ms']:>10.2f}{linha['tempo_minimo_ms']:>10.2f}"
            f"{linha['ganho_vs_pura_%']:>+10.1f}"
        )
    print(f"\nmelhor corte.......: {melhor['configuracao']} ({melhor['tempo_medio_ms']:.2f} ms)")
    print(f"rapida pura........: {base['tempo_medio_ms']:.2f} ms")
    print(f"ganho do melhor....: {melhor['ganho_vs_pura_%']:+.1f}%")
    print(f"corte=1 vs pura....: {linhas[1]['tempo_medio_ms']:.2f} ms vs {base['tempo_medio_ms']:.2f} ms")
    print(f"pior corte.........: {pior['configuracao']} ({pior['tempo_medio_ms']:.2f} ms, {pior['ganho_vs_pura_%']:+.1f}%)")


if __name__ == "__main__":
    main()
