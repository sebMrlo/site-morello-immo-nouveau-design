# -*- coding: utf-8 -*-
"""Règles d'arrondi (règles métier 1 à 5)."""
from decimal import Decimal

import pytest

import facture_gen
from facture_gen import ht, r2


def test_base_ht_par_ligne():
    # TTC / 1,2, ROUND_HALF_UP à 2 décimales
    assert ht(542.51) == Decimal("452.09")
    assert ht(630.28) == Decimal("525.23")
    assert ht(850.00) == Decimal("708.33")
    assert ht(899.00) == Decimal("749.17")
    assert ht(770.00) == Decimal("641.67")
    assert ht(690.00) == Decimal("575.00")


def test_totaux_quietis_juillet_reels():
    # Valeurs de la facture réelle F-2026-07-001.
    entrees = [
        ("03/07/2026", "BELKHARCHOUCHE", "NELYA", "A202", Decimal("542.51")),
        ("07/07/2026", "RODRIGUES-JADOT", "NELYA", "B103", Decimal("690.00")),
        ("07/07/2026", "ANDRE", "RUE DORÉE", "2E", Decimal("630.28")),
        ("17/07/2026", "SERBON", "NELYA", "B202", Decimal("850.00")),
        ("21/07/2026", "REMMACH", "ALTHEA", "B108", Decimal("899.00")),
        ("21/07/2026", "ANGONNET", "NELYA", "B006", Decimal("770.00")),
    ]
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        total_ttc, total_ht, part = facture_gen.generer(
            path=path, numero="F-2026-07-001", date="01/07/2026",
            objet="o", entrees=entrees, societe="QUIETIS")
    finally:
        os.remove(path)
    assert total_ttc == Decimal("4381.79")
    assert total_ht == Decimal("3651.49")   # somme des bases HT arrondies
    assert part == Decimal("1825.75")       # TTC / 1,2 / 2, arrondi à la fin


def test_part_50_arrondie_a_la_fin_pas_sur_le_ht():
    """Règle 3 : la part 50 % = total_TTC/1,2/2 arrondi SEULEMENT à la fin.

    Diviser le total HT déjà arrondi donnerait un écart d'un centime. C'est le cas
    de divergence rencontré sur la facture de juin 2026 (part correcte de l'ordre
    du « 2 152,40 € » plutôt qu'un centime au-dessus). Jeu minimal reproduisant
    l'écart :
    """
    combo = [Decimal("400.00"), Decimal("400.28"), Decimal("450.51")]
    total_ttc = sum(combo)                              # 1250.79
    naive = r2(sum(ht(t) for t in combo) / 2)           # via HT arrondi -> 521.17
    correct = r2(total_ttc / Decimal("1.2") / 2)        # à la fin        -> 521.16
    assert naive == Decimal("521.17")
    assert correct == Decimal("521.16")
    assert naive != correct

    import tempfile, os
    entrees = [("01/06/2026", "X", "Y", "Z", t) for t in combo]
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        _, _, part = facture_gen.generer(
            path=path, numero="F-2026-06-000", date="01/06/2026",
            objet="o", entrees=entrees, societe="QUIETIS")
    finally:
        os.remove(path)
    assert part == correct  # le moteur suit bien la règle 3


def test_tva_nulle_total_a_payer_egal_part():
    # Règles 4 et 5 : TVA = 0, TOTAL À PAYER = part HT à 50 %.
    assert facture_gen.eur(0) == "0,00 €"
