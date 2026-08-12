# -*- coding: utf-8 -*-
"""Données de référence Juillet 2026 (issues des factures réelles F-2026-07-001/002)
et construction de la facture QUIETIS servant de « golden » au test de non-régression.
"""
from decimal import Decimal

import facture_gen

# Lignes de la facture QUIETIS de juillet, telles que produites par le pipeline
# (patronymes normalisés, résidences en majuscules, dates jj/mm/aaaa).
QUIETIS_JUILLET = [
    ("03/07/2026", "BELKHARCHOUCHE", "NELYA", "A202", Decimal("542.51")),
    ("07/07/2026", "RODRIGUES-JADOT", "NELYA", "B103", Decimal("690.00")),
    ("07/07/2026", "ANDRE", "RUE DORÉE", "2E", Decimal("630.28")),
    ("17/07/2026", "SERBON", "NELYA", "B202", Decimal("850.00")),
    ("21/07/2026", "REMMACH", "ALTHEA", "B108", Decimal("899.00")),
    ("21/07/2026", "ANGONNET", "NELYA", "B006", Decimal("770.00")),
]

GOLDEN_META = dict(
    numero="F-2026-07-001",
    date="01/07/2026",
    objet="Commission d'honoraires - Juillet 2026 - QUIETIS",
    societe="QUIETIS",
)


def build_golden(path):
    """Génère la facture QUIETIS de référence à l'emplacement `path`."""
    return facture_gen.generer(path=str(path), entrees=QUIETIS_JUILLET, **GOLDEN_META)
