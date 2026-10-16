"""Testes de correção dos algoritmos (stdlib apenas).

Uso: python3 -m tests.test_ordenacoes
"""

from __future__ import annotations

import random
import statistics
import unittest

from src.ordenacoes import insercao, quicksort_hibrido, quicksort_puro

CORTES = [1, 5, 10, 16, 20, 32, 50, 100, 200]


def casos() -> list[list[int]]:
    rng = random.Random(123)
    return [
        [],
        [1],
        [2, 1],
        [5, 5, 5, 5],
        [3, 1, 2, 1, 3, 2, 1],
        list(range(50)),
        list(range(50, 0, -1)),
        [rng.randint(0, 20) for _ in range(500)],
        [rng.randint(0, 10_000) for _ in range(2_000)],
    ]


class TestesOrdenacao(unittest.TestCase):
    def test_insercao(self):
        for entrada in casos():
            self.assertEqual(insercao(list(entrada)), sorted(entrada))

    def test_quicksort_puro(self):
        for entrada in casos():
            self.assertEqual(quicksort_puro(list(entrada), random.Random(1)), sorted(entrada))

    def test_quicksort_hibrido_todos_os_cortes(self):
        for corte in CORTES:
            for entrada in casos():
                self.assertEqual(
                    quicksort_hibrido(list(entrada), corte, random.Random(1)),
                    sorted(entrada),
                    msg=f"falhou com corte={corte} e entrada de tamanho {len(entrada)}",
                )

    def test_corte_invalido(self):
        with self.assertRaises(ValueError):
            quicksort_hibrido([3, 1, 2], 0)

    def test_hibrido_com_corte_1_iguala_a_pura(self):
        """Com corte = 1 a inserção nunca é acionada: as duas devem coincidir exatamente."""
        for entrada in casos():
            pura = quicksort_puro(list(entrada), random.Random(5))
            hibrida = quicksort_hibrido(list(entrada), 1, random.Random(5))
            self.assertEqual(pura, hibrida)

    def test_ordena_no_lugar(self):
        """As funções ordenam o próprio vetor e devolvem o mesmo objeto."""
        for ordenar in (quicksort_puro, lambda l: quicksort_hibrido(l, 16)):
            vetor = [3, 1, 2]
            resultado = ordenar(vetor)
            self.assertIs(resultado, vetor)
            self.assertEqual(vetor, [1, 2, 3])

    def test_insercao_so_e_acionada_quando_corte_maior_que_1(self):
        """corte = 1 nunca chama a inserção; corte > 1 chama, e em pedaços menores."""
        from src import ordenacoes

        original = ordenacoes.insercao
        tamanhos: list[int] = []

        def registrando(lista, inicio=0, fim=None):
            tamanhos.append((fim if fim is not None else len(lista) - 1) - inicio + 1)
            return original(lista, inicio, fim)

        vetor = [random.Random(i).randint(0, 100_000) for i in range(5_000)]
        try:
            ordenacoes.insercao = registrando

            tamanhos.clear()
            quicksort_hibrido(list(vetor), 1, random.Random(7))
            self.assertEqual(tamanhos, [], "corte = 1 não deveria chamar a inserção")

            tamanhos.clear()
            quicksort_hibrido(list(vetor), 16, random.Random(7))
            pedacos_16 = list(tamanhos)
            self.assertGreater(len(pedacos_16), 0)
            self.assertTrue(all(t < 16 for t in pedacos_16))

            tamanhos.clear()
            quicksort_hibrido(list(vetor), 200, random.Random(7))
            pedacos_200 = list(tamanhos)
        finally:
            ordenacoes.insercao = original

        # corte maior -> menos pedaços, porém maiores (é isso que encarece a inserção)
        self.assertLess(len(pedacos_200), len(pedacos_16))
        self.assertGreater(statistics.fmean(pedacos_200), statistics.fmean(pedacos_16))

    def test_vetor_grande_nao_estoura_a_pilha(self):
        """200 mil elementos: a recursão no lado menor mantém a pilha em O(log n)."""
        dados = [random.Random(4).randint(0, 2_000_000) for _ in range(200_000)]
        esperado = sorted(dados)
        casos = (
            lambda l, r: quicksort_puro(l, r),
            lambda l, r: quicksort_hibrido(l, 1, r),
            lambda l, r: quicksort_hibrido(l, 32, r),
        )
        for ordenar in casos:
            self.assertEqual(ordenar(list(dados), random.Random(2)), esperado)

    def test_corte_1_faz_o_mesmo_numero_de_particoes_da_pura(self):
        """Reforça a equivalência: mesmo vetor, mesma semente, mesmas partições."""
        from src import ordenacoes

        original = ordenacoes._particionar_tres_vias
        for entrada in casos():
            contagens = []
            for chamada in (quicksort_puro, lambda l, r: quicksort_hibrido(l, 1, r)):
                contador = [0]

                def contando(*args, _c=contador, _o=original):
                    _c[0] += 1
                    return _o(*args)

                ordenacoes._particionar_tres_vias = contando
                try:
                    chamada(list(entrada), random.Random(5))
                finally:
                    ordenacoes._particionar_tres_vias = original
                contagens.append(contador[0])
            self.assertEqual(
                contagens[0], contagens[1],
                msg=f"numero de particoes diferente para entrada de tamanho {len(entrada)}",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
