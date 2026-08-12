# -*- coding: utf-8 -*-
"""CLI : contrôle de cohérence (garde-fou) et numérotation continue."""
import json
from decimal import Decimal

import pytest

import facture
from make_fixture import make


def _compteur(tmp_path, valeur=2):
    p = tmp_path / "compteur.json"
    p.write_text(json.dumps({"2026": valeur}), encoding="utf-8")
    return p


def test_run_nominal_genere_deux_factures(tmp_path):
    pdf = make(tmp_path / "e.pdf")
    out = tmp_path / "out"
    compteur = _compteur(tmp_path, valeur=2)

    code = facture.main([str(pdf), "--out", str(out), "--compteur", str(compteur)])
    assert code == 0

    q = out / "Facture_QUIETIS_GESTION_Juillet_2026.pdf"
    s = out / "Facture_SNG_GROUPE_Juillet_2026.pdf"
    assert q.exists() and s.exists()

    # numérotation continue : 002 était le dernier -> 003 (QUIETIS) puis 004 (SNG)
    assert json.loads(compteur.read_text())["2026"] == 4


def test_ordre_numeros_suit_premiere_apparition(tmp_path):
    pdf = make(tmp_path / "e.pdf")
    out = tmp_path / "out"
    compteur = _compteur(tmp_path, valeur=2)
    res = facture.parse_entrees(str(pdf))
    resultats = facture.generer_factures(res, out, compteur)
    numeros = {r["societe"]: r["numero"] for r in resultats}
    assert numeros["QUIETIS"] == "F-2026-07-003"   # QUIETIS apparaît en premier
    assert numeros["SNG"] == "F-2026-07-004"


def test_ecart_total_interrompt_sans_rien_ecrire(tmp_path, capsys):
    # total imprimé volontairement faux -> le garde-fou doit stopper
    pdf = make(tmp_path / "e.pdf", total="9 999,99 €")
    out = tmp_path / "out"
    compteur = _compteur(tmp_path, valeur=2)

    code = facture.main([str(pdf), "--out", str(out), "--compteur", str(compteur)])
    assert code == 1

    # aucun PDF, compteur inchangé
    assert not (out / "Facture_QUIETIS_GESTION_Juillet_2026.pdf").exists()
    assert json.loads(compteur.read_text())["2026"] == 2
    sortie = capsys.readouterr().out
    assert "ÉCART" in sortie


def test_numerotation_continue_sur_deux_runs(tmp_path):
    pdf = make(tmp_path / "e.pdf")
    out = tmp_path / "out"
    compteur = _compteur(tmp_path, valeur=2)

    facture.main([str(pdf), "--out", str(out), "--compteur", str(compteur)])
    assert json.loads(compteur.read_text())["2026"] == 4
    # deuxième passage : la séquence continue (005, 006)
    res = facture.parse_entrees(str(pdf))
    resultats = facture.generer_factures(res, out, compteur)
    assert [r["numero"] for r in resultats] == ["F-2026-07-005", "F-2026-07-006"]
    assert json.loads(compteur.read_text())["2026"] == 6


def test_dry_run_n_ecrit_rien(tmp_path):
    pdf = make(tmp_path / "e.pdf")
    out = tmp_path / "out"
    compteur = _compteur(tmp_path, valeur=2)

    code = facture.main([str(pdf), "--out", str(out), "--compteur", str(compteur), "--dry-run"])
    assert code == 0
    assert not (out / "Facture_QUIETIS_GESTION_Juillet_2026.pdf").exists()
    assert json.loads(compteur.read_text())["2026"] == 2  # compteur intact
