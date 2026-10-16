"""Algoritmos de ordenação usados no estudo da ordenação híbrida.

Contém três peças:

* ``insercao``          -- ordenação por inserção, usada nos pedaços pequenos;
* ``quicksort_puro``    -- ordenação rápida com pivô aleatório (sempre rápida);
* ``quicksort_hibrido`` -- ordenação rápida que delega para a inserção
                           quando o pedaço tem menos que ``corte`` elementos.

A partição usada é a de três vias (menores / iguais / maiores), o que evita
o pior caso quando há muitos elementos repetidos.
"""

from __future__ import annotations

import random

__all__ = ["insercao", "quicksort_puro", "quicksort_hibrido"]


def insercao(lista: list, inicio: int = 0, fim: int | None = None) -> list:
    """Ordena ``lista[inicio:fim+1]`` no lugar pelo método de inserção.

    O intervalo é fechado nas duas pontas, para poder ser chamada sobre um
    pedaço de um vetor maior sem precisar copiar dados.
    """
    if fim is None:
        fim = len(lista) - 1
    for i in range(inicio + 1, fim + 1):
        chave = lista[i]
        j = i - 1
        while j >= inicio and lista[j] > chave:
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = chave
    return lista


def _particionar_tres_vias(lista: list, inicio: int, fim: int, rng: random.Random):
    """Particiona ``lista[inicio:fim]`` em menores, iguais e maiores que o pivô.

    O pivô é escolhido aleatoriamente e trocado para a posição ``inicio``.
    Devolve o intervalo fechado ``(primeiro_igual, ultimo_igual)`` ocupado
    pelos elementos iguais ao pivô.
    """
    indice_pivo = rng.randint(inicio, fim)
    lista[inicio], lista[indice_pivo] = lista[indice_pivo], lista[inicio]
    pivo = lista[inicio]

    menores = inicio          # lista[inicio:menores]  < pivo
    i = inicio + 1            # lista[menores:i]      == pivo
    maiores = fim + 1         # lista[maiores:fim+1]   > pivo

    while i < maiores:
        if lista[i] < pivo:
            lista[i], lista[menores] = lista[menores], lista[i]
            menores += 1
            i += 1
        elif lista[i] > pivo:
            maiores -= 1
            lista[i], lista[maiores] = lista[maiores], lista[i]
        else:
            i += 1

    return menores, maiores - 1


def quicksort_puro(lista: list, rng: random.Random | None = None) -> list:
    """Ordenação rápida pura: nunca chama a inserção, por mais curto que seja o pedaço."""
    if rng is None:
        rng = random.Random()
    _puro(lista, 0, len(lista) - 1, rng)
    return lista


def _puro(lista: list, inicio: int, fim: int, rng: random.Random) -> None:
    while inicio < fim:
        menores, maiores = _particionar_tres_vias(lista, inicio, fim, rng)
        # Recursão sempre no lado menor e laço no lado maior: limita a
        # profundidade da pilha a O(log n).
        if menores - inicio < fim - maiores:
            _puro(lista, inicio, menores - 1, rng)
            inicio = maiores + 1
        else:
            _puro(lista, maiores + 1, fim, rng)
            fim = menores - 1


def quicksort_hibrido(lista: list, corte: int = 1, rng: random.Random | None = None) -> list:
    """Ordenação híbrida: rápida para pedaços grandes, inserção para pedaços pequenos.

    ``corte`` é o limiar de troca. Sempre que um pedaço tiver menos que
    ``corte`` elementos, a inserção assume o serviço.

    Com ``corte = 1`` nenhum pedaço tem menos que 1 elemento, então a
    inserção nunca é chamada e o resultado é a ordenação rápida pura
    (mesmas decisões de partição, mesmo número de operações).
    """
    if corte < 1:
        raise ValueError("corte deve ser >= 1")
    if rng is None:
        rng = random.Random()
    _hibrido(lista, 0, len(lista) - 1, corte, rng)
    return lista


def _hibrido(lista: list, inicio: int, fim: int, corte: int, rng: random.Random) -> None:
    while inicio < fim:
        if fim - inicio + 1 < corte:
            insercao(lista, inicio, fim)
            return
        menores, maiores = _particionar_tres_vias(lista, inicio, fim, rng)
        if menores - inicio < fim - maiores:
            _hibrido(lista, inicio, menores - 1, corte, rng)
            inicio = maiores + 1
        else:
            _hibrido(lista, maiores + 1, fim, corte, rng)
            fim = menores - 1
