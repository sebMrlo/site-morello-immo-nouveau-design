# -*- coding: utf-8 -*-
"""Test de non-régression du moteur de rendu (facture_gen).

Régénère la facture QUIETIS de juillet 2026 et vérifie que la position de chaque
mot (via pdfplumber.extract_words) correspond au PDF de référence « golden » au
0,1 pt près. Ce test doit rester vert : toute dérive géométrique de facture_gen.py
le fait échouer immédiatement.

Le golden a été produit par ce même moteur ; ses valeurs chiffrées (Base HT, totaux)
sont par ailleurs identiques, au centime, à la facture réelle F-2026-07-001.
"""
from pathlib import Path

import pdfplumber
import pytest

from reference import build_golden

GOLDEN = Path(__file__).parent / "golden" / "Facture_QUIETIS_Juillet_2026.pdf"
TOL = 0.1  # points


def _words(path):
    with pdfplumber.open(str(path)) as pdf:
        page = pdf.pages[0]
        return [
            (w["text"], round(w["x0"], 3), round(w["top"], 3))
            for w in page.extract_words(use_text_flow=False, keep_blank_chars=False)
        ]


def test_golden_existe():
    assert GOLDEN.exists(), "Le PDF de référence golden est manquant."


def test_positions_mots_identiques(tmp_path):
    regen = tmp_path / "regen.pdf"
    build_golden(regen)

    ref = _words(GOLDEN)
    got = _words(regen)

    assert len(got) == len(ref), (
        f"Nombre de mots différent : {len(got)} vs {len(ref)} (référence)."
    )
    for (t_ref, x_ref, y_ref), (t_got, x_got, y_got) in zip(ref, got):
        assert t_got == t_ref, f"Texte différent : {t_got!r} vs {t_ref!r}"
        assert abs(x_got - x_ref) <= TOL, (
            f"x de {t_ref!r} : {x_got} vs {x_ref} (>|{TOL}|)"
        )
        assert abs(y_got - y_ref) <= TOL, (
            f"y de {t_ref!r} : {y_got} vs {y_ref} (>|{TOL}|)"
        )
