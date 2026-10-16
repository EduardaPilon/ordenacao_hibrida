"""Valida a consistência entre os dados medidos e o que o relatório afirma.

Confere, sem depender de bibliotecas externas:

* o CSV: a coluna de ganho bate com os tempos medidos;
* ``tabela.md`` e a tabela do ``RELATORIO.md`` reproduzem os números do CSV;
* o melhor corte apontado no relatório é realmente o menor tempo medido;
* o gráfico existe e é um PNG válido;
* o relatório contém as afirmações-chave (melhor corte, ganho, corte = 1
  equivalente à rápida pura, degradação nos cortes grandes).

Uso: python3 -m tests.validar_artefatos
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"

falhas: list[str] = []


def checar(nome: str, condicao: bool, extra: str = "") -> None:
    print(("  OK   " if condicao else "  FALHA") + f"  {nome}" + (f"  -> {extra}" if extra else ""))
    if not condicao:
        falhas.append(nome)


def normalizar(texto: str) -> str:
    """Deixa os números comparáveis: sem markdown, sem acentos, vírgula decimal,
    menos unicode."""
    texto = texto.replace("*", "").replace("\u2212", "-").replace(",", ".")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.split())


def ler_csv() -> dict[str, dict]:
    with (RESULTADOS / "tempos.csv").open(encoding="utf-8") as arquivo:
        return {linha["configuracao"]: linha for linha in csv.DictReader(arquivo)}


def linhas_de_tabela(caminho: Path) -> list[list[str]]:
    linhas = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if linha.strip().startswith("|"):
            celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
            if celulas and not set("".join(celulas)) <= set("-: "):
                linhas.append(celulas)
    return linhas


def nome_interno(rotulo: str) -> str:
    limpo = normalizar(rotulo).lower()
    if limpo.startswith("rapida") or limpo.startswith("pura"):
        return "pura"
    encontrado = re.search(r"corte\s*=\s*(\d+)", limpo)
    if encontrado:
        return f"hibrida {encontrado.group(1)}"
    return limpo


def main() -> None:
    dados = ler_csv()
    esperado_pura = float(dados["pura"]["tempo_medio_ms"])

    print("1) tempos.csv: ganho recalculado a partir dos tempos")
    for nome, linha in dados.items():
        recalculado = (esperado_pura - float(linha["tempo_medio_ms"])) / esperado_pura * 100.0
        declarado = float(linha["ganho_vs_pura_%"])
        checar(f"{nome}: ganho {declarado:+.2f}%", abs(recalculado - declarado) < 0.01)

    print("2) tempos.csv: tempo minimo <= media e desvio >= 0")
    for nome, linha in dados.items():
        checar(
            f"{nome}: min <= media, desvio >= 0",
            float(linha["tempo_minimo_ms"]) <= float(linha["tempo_medio_ms"])
            and float(linha["desvio_ms"]) >= 0,
        )

    print("3) resultados/tabela.md reproduz o CSV")
    for celulas in linhas_de_tabela(RESULTADOS / "tabela.md")[1:]:
        nome = nome_interno(celulas[0])
        linha = dados[nome]
        esperados = [
            f"{float(linha['tempo_medio_ms']):.2f}",
            f"{float(linha['desvio_ms']):.2f}",
            f"{float(linha['tempo_minimo_ms']):.2f}",
            f"{float(linha['ganho_vs_pura_%']):+.1f}",
        ]
        obtidos = [normalizar(c) for c in celulas[1:5]]
        checar(f"{nome}: {obtidos}", obtidos == esperados, f"esperado {esperados}")

    print("4) RELATORIO.md: tabela de resultados reproduz o CSV")
    relatorio = (RAIZ / "RELATORIO.md").read_text(encoding="utf-8")
    linhas = linhas_de_tabela(RAIZ / "RELATORIO.md")
    linhas_resultado = [c for c in linhas if nome_interno(c[0]) in dados]
    checar("tabela do relatorio encontrada", len(linhas_resultado) == len(dados),
          f"{len(linhas_resultado)} de {len(dados)} linhas")
    for celulas in linhas_resultado:
        nome = nome_interno(celulas[0])
        linha = dados[nome]
        esperados = [
            f"{float(linha['tempo_medio_ms']):.2f}",
            f"{float(linha['desvio_ms']):.2f}",
            f"{float(linha['tempo_minimo_ms']):.2f}",
            f"{float(linha['ganho_vs_pura_%']):+.1f}",
        ]
        obtidos = [normalizar(c) for c in celulas[1:5]]
        checar(f"{nome}: {obtidos}", obtidos == esperados, f"esperado {esperados}")

    print("5) RELATORIO.md: melhor corte apontado = menor tempo medido")
    melhor = min((c for c in dados if c != "pura"), key=lambda c: float(dados[c]["tempo_medio_ms"]))
    melhor_corte = melhor.split()[1]
    pura = float(dados["pura"]["tempo_medio_ms"])
    ganho = (pura - float(dados[melhor]["tempo_medio_ms"])) / pura * 100.0
    checar(f"melhor medido = corte {melhor_corte}", True)
    checar(f"relatorio aponta corte = {melhor_corte}", f"corte = {melhor_corte}" in relatorio)
    checar(f"relatorio cita o ganho {ganho:+.1f}%",
           f"{ganho:.1f}".replace(".", ",") in relatorio)
    checar("relatorio cita o tempo da rapida pura",
           f"{pura:.2f}".replace(".", ",") in relatorio)

    print("6) RELATORIO.md: corte = 1 equivalente a rapida pura")
    t1 = float(dados["hibrida 1"]["tempo_medio_ms"])
    desvio = float(dados["pura"]["desvio_ms"])
    checar("tempo de corte=1 dentro do desvio padrao da pura", abs(t1 - pura) <= desvio,
           f"|{t1:.2f} - {pura:.2f}| <= {desvio:.2f}")

    print("7) RELATORIO.md: degradacao nos cortes grandes")
    pior = max((c for c in dados if c != "pura"), key=lambda c: float(dados[c]["tempo_medio_ms"]))
    pior_tempo = float(dados[pior]["tempo_medio_ms"])
    checar("corte=100 mais lento que a pura", float(dados["hibrida 100"]["tempo_medio_ms"]) > pura)
    checar("corte=200 e o pior de todos", pior == "hibrida 200", pior)
    checar(f"relatorio cita o pior tempo {pior_tempo:.2f} ms",
           f"{pior_tempo:.2f}".replace(".", ",") in relatorio)

    print("8) grafico")
    png = (RESULTADOS / "tempo_vs_corte.png").read_bytes()
    checar("tempo_vs_corte.png e um PNG valido", png[:8] == b"\x89PNG\r\n\x1a\n",
           f"{len(png)} bytes")

    print()
    if falhas:
        print(f"RESULTADO: {len(falhas)} FALHA(S): {falhas}")
        sys.exit(1)
    print("RESULTADO: TUDO OK")


if __name__ == "__main__":
    main()
