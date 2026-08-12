# -*- coding: utf-8 -*-
"""Extraction de bout en bout du PDF « Entrées du mois » (fixture synthétique)."""
from decimal import Decimal

import pytest

from make_fixture import make
from parser import parse_entrees


@pytest.fixture
def pdf_juillet(tmp_path):
    return make(tmp_path / "entrees_juillet_2026.pdf")


def test_periode_detectee(pdf_juillet):
    res = parse_entrees(pdf_juillet)
    assert res.mois == 7
    assert res.annee == 2026


def test_nombre_de_lignes_et_total(pdf_juillet):
    res = parse_entrees(pdf_juillet)
    assert len(res.entrees) == 7
    assert res.total_source == Decimal("4831.79")
    assert res.total_extrait == res.total_source


def test_lignes_normalisees(pdf_juillet):
    res = parse_entrees(pdf_juillet)
    lignes = [(e.date, e.nom, e.residence, e.lot, e.ttc, e.societe) for e in res.entrees]
    assert lignes == [
        ("03/07/2026", "BELKHARCHOUCHE", "NELYA", "A202", Decimal("542.51"), "QUIETIS"),
        ("07/07/2026", "RODRIGUES-JADOT", "NELYA", "B103", Decimal("690.00"), "QUIETIS"),
        ("07/07/2026", "ANDRE", "RUE DORÉE", "2E", Decimal("630.28"), "QUIETIS"),
        ("13/07/2026", "DIAFI", "RUE COLBERT", "1", Decimal("450.00"), "SNG"),
        ("17/07/2026", "SERBON", "NELYA", "B202", Decimal("850.00"), "QUIETIS"),
        ("21/07/2026", "REMMACH", "ALTHEA", "B108", Decimal("899.00"), "QUIETIS"),
        ("21/07/2026", "ANGONNET", "NELYA", "B006", Decimal("770.00"), "QUIETIS"),
    ]


def test_toutes_les_lignes_fiables(pdf_juillet):
    res = parse_entrees(pdf_juillet)
    assert all(e.nom_fiable for e in res.entrees)
    assert res.avertissements == []
