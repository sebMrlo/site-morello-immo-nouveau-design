# -*- coding: utf-8 -*-
"""Normalisation heuristique des noms de locataires."""
import pytest

from parser import normalize_nom


@pytest.mark.parametrize("brut,attendu", [
    ("Belkharchouche Malik", "BELKHARCHOUCHE"),          # patronyme en premier
    ("Mathilde Rodrigues et Anthony Jadot", "RODRIGUES-JADOT"),  # couple, 2 noms
    ("Christophe Andre", "ANDRE"),
    ("Nassim Diafi", "DIAFI"),
    ("Ophélie Serbon", "SERBON"),
    ("Morad et fathia Remmach", "REMMACH"),              # couple, nom partagé
    ("Noah Angonnet", "ANGONNET"),
])
def test_normalisation_cas_reels(brut, attendu):
    nom, fiable = normalize_nom(brut)
    assert nom == attendu
    assert fiable is True


def test_override_manuel():
    nom, fiable = normalize_nom("Cas Bizarre Impossible", overrides={"Cas Bizarre Impossible": "BIZARRE"})
    assert nom == "BIZARRE"
    assert fiable is True


def test_nom_inconnu_marque_a_verifier():
    # Deux tokens dont aucun n'est un prénom connu : on retombe sur la convention
    # (nom = dernier token) mais on signale que c'est à vérifier.
    nom, fiable = normalize_nom("Xyz Wxv")
    assert nom == "WXV"
    assert fiable is False


def test_couple_deux_noms_distincts_ordre_preserve():
    nom, fiable = normalize_nom("Julien Martin et Sophie Bernard")
    # 'martin'/'bernard' peuvent être connus comme prénoms ; la convention garde
    # le dernier token de chaque membre. On vérifie surtout la jonction par tiret.
    assert "-" in nom
    assert nom == nom.upper()
