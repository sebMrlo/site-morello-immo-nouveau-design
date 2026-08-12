# -*- coding: utf-8 -*-
"""Parsing des dates, des montants et format monétaire."""
from decimal import Decimal

import pytest

from facture_gen import eur
from parser import parse_date, parse_montant


@pytest.mark.parametrize("brut,attendu", [
    ("03-juil-26", "03/07/2026"),
    ("3-juil-26", "03/07/2026"),
    ("13-juil-26", "13/07/2026"),
    ("1-janv-26", "01/01/2026"),
    ("07-août-26", "07/08/2026"),
    ("07-aout-26", "07/08/2026"),
    ("21-déc-25", "21/12/2025"),
    ("28-févr-26", "28/02/2026"),
    ("15-sept-2026", "15/09/2026"),
    ("05/mai/26", "05/05/2026"),
])
def test_parse_date(brut, attendu):
    assert parse_date(brut) == attendu


def test_parse_date_invalide():
    with pytest.raises(ValueError):
        parse_date("pas une date")
    with pytest.raises(ValueError):
        parse_date("03-xxx-26")


@pytest.mark.parametrize("brut,attendu", [
    ("542,51 €", Decimal("542.51")),
    ("690,00 €", Decimal("690.00")),
    ("4 831,79 €", Decimal("4831.79")),
    ("4 831,79 €", Decimal("4831.79")),   # espace fine insécable
    ("4 831,79 €", Decimal("4831.79")),   # espace insécable
    ("1 250,79 €", Decimal("1250.79")),
    ("450,00", Decimal("450.00")),
    ("12 345 678,90 €", Decimal("12345678.90")),
])
def test_parse_montant(brut, attendu):
    assert parse_montant(brut) == attendu


def test_parse_montant_invalide():
    with pytest.raises(ValueError):
        parse_montant("aucun chiffre ici")


@pytest.mark.parametrize("val,attendu", [
    (Decimal("1825.75"), "1 825,75 €"),
    (Decimal("187.50"), "187,50 €"),
    (Decimal("450.00"), "450,00 €"),
    (0, "0,00 €"),
    (Decimal("12345678.90"), "12 345 678,90 €"),
])
def test_format_monetaire_francais(val, attendu):
    assert eur(val) == attendu
