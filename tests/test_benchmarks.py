"""Test poprawnosci (nie wydajnosci - czas nie jest tu asercja, bo byloby
niestabilne w CI) dla benchmarks/parallel_vs_sequential.py: sekwencyjne
i rownolegle przetworzenie tych samych danych musi dawac identyczny wynik."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmarks.parallel_vs_sequential import run_comparison


def test_sequential_and_parallel_give_identical_results_small():
    # run_comparison() sam w sobie assertuje zgodnosc wynikow (sorted(seq) == sorted(par)) -
    # tu tylko potwierdzamy, ze nie rzuca i zwraca sensowne liczby na malym N.
    r = run_comparison(total_words=400, n_streams=2, seed=1)
    assert r["seq_rate"] > 0
    assert r["par_rate"] > 0
    assert r["n_streams"] == 2
    assert r["total_words"] == 400
