#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI de facturation SNG / QUIETIS.

    python facture.py entrees_aout_2026.pdf

Lit le PDF « Entrées du mois », vérifie la cohérence du total, puis génère une
facture de commission par société dans ./out/, en incrémentant la numérotation
(compteur.json). Le rendu PDF est délégué à facture_gen.generer (non modifié).
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

import facture_gen
from parser import (
    MOIS_AFFICHE,
    MOIS_SLUG,
    ParseResult,
    ParserError,
    load_overrides,
    parse_entrees,
)

# Correspondance société (colonne) -> bloc CLIENT du module de rendu.
SOCIETES = {
    "QUIETIS": "QUIETIS",
    "SNG": "SNG",
}


def client_slug(societe: str) -> str:
    """QUIETIS -> 'QUIETIS_GESTION', SNG -> 'SNG_GROUPE' (2e ligne du bloc CLIENT)."""
    bloc = facture_gen.CLIENTS[societe]
    return bloc[1].replace(" ", "_")


# ----------------------------------------------------------------- compteur
def charger_compteur(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def sauver_compteur(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def ordre_societes(res: ParseResult) -> list[str]:
    """Ordre des sociétés selon leur première apparition dans le PDF source."""
    ordre = []
    for e in res.entrees:
        if e.societe not in ordre:
            ordre.append(e.societe)
    return ordre


# ----------------------------------------------------------------- affichage
def _fmt(montant: Decimal) -> str:
    return facture_gen.eur(montant)


def recap_noms(res: ParseResult) -> None:
    print("\nNormalisation des noms (à vérifier) :")
    largeur = max((len(e.nom_raw) for e in res.entrees), default=0)
    for e in res.entrees:
        drapeau = "  " if e.nom_fiable else "⚠ "
        print(f"  {drapeau}{e.nom_raw:<{largeur}}  ->  {e.nom}")
    for av in res.avertissements:
        print(f"  ⚠  {av}")


def controle_coherence(res: ParseResult) -> bool:
    extrait = res.total_extrait
    source = res.total_source
    ok = extrait == source
    print("\nContrôle de cohérence :")
    print(f"  Somme des honoraires extraits : {_fmt(extrait)}")
    print(f"  Total imprimé sur le PDF       : {_fmt(source)}")
    if ok:
        print("  ✓ Les totaux correspondent.")
    else:
        ecart = (extrait - source).copy_abs()
        print(f"  ✗ ÉCART de {_fmt(ecart)} — génération interrompue, rien n'est écrit.")
    return ok


# ----------------------------------------------------------------- génération
def generer_factures(res: ParseResult, out_dir: Path, compteur_path: Path,
                     dry_run: bool = False) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    compteur = charger_compteur(compteur_path)
    annee = res.annee
    seq = int(compteur.get(str(annee), 0))

    resultats = []
    for societe in ordre_societes(res):
        lignes = [e for e in res.entrees if e.societe == societe]
        seq += 1
        numero = f"F-{annee}-{res.mois:02d}-{seq:03d}"
        objet = f"Commission d'honoraires - {MOIS_AFFICHE[res.mois]} {annee} - {societe}"
        date_fac = f"01/{res.mois:02d}/{annee}"
        nom_fichier = f"Facture_{client_slug(societe)}_{MOIS_SLUG[res.mois]}_{annee}.pdf"
        chemin = out_dir / nom_fichier

        entrees_tuples = [(e.date, e.nom, e.residence, e.lot, e.ttc) for e in lignes]

        if not dry_run:
            total_ttc, total_ht, part = facture_gen.generer(
                path=str(chemin),
                numero=numero,
                date=date_fac,
                objet=objet,
                entrees=entrees_tuples,
                societe=SOCIETES[societe],
            )
        else:
            total_ttc = sum((facture_gen.r2(e.ttc) for e in lignes), Decimal("0"))
            total_ht = sum((facture_gen.ht(e.ttc) for e in lignes), Decimal("0"))
            part = facture_gen.r2(total_ttc / Decimal("1.2") / 2)

        resultats.append({
            "societe": societe,
            "n_lignes": len(lignes),
            "numero": numero,
            "total_ttc": total_ttc,
            "total_ht": total_ht,
            "part": part,
            "fichier": str(chemin),
        })

    if not dry_run:
        compteur[str(annee)] = seq
        sauver_compteur(compteur_path, compteur)

    return resultats


def recap_factures(resultats: list[dict], dry_run: bool) -> None:
    titre = "Factures qui seraient générées (dry-run) :" if dry_run else "Factures générées :"
    print(f"\n{titre}")
    for r in resultats:
        print(
            f"  {r['societe']:<8} | {r['n_lignes']:>2} ligne(s) | "
            f"TTC {_fmt(r['total_ttc']):>12} | HT {_fmt(r['total_ht']):>12} | "
            f"Part 50% {_fmt(r['part']):>12} | {r['numero']} | {r['fichier']}"
        )


# ----------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Génère les factures de commission SNG/QUIETIS.")
    ap.add_argument("pdf", help="PDF « Entrées du mois » (LIFESTONE).")
    ap.add_argument("--out", default="out", help="Dossier de sortie (défaut: out).")
    ap.add_argument("--compteur", default="compteur.json",
                    help="Fichier de numérotation (défaut: compteur.json).")
    ap.add_argument("--overrides", default="noms_overrides.json",
                    help="Corrections manuelles de noms (optionnel).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Analyse et contrôle sans écrire de PDF ni toucher au compteur.")
    args = ap.parse_args(argv)

    try:
        overrides = load_overrides(args.overrides)
        res = parse_entrees(args.pdf, overrides=overrides)
    except (ParserError, FileNotFoundError) as exc:
        print(f"Erreur de lecture du PDF source : {exc}", file=sys.stderr)
        return 2

    print(f"Période détectée : {MOIS_AFFICHE[res.mois]} {res.annee}")
    print(f"Lignes extraites : {len(res.entrees)}")
    recap_noms(res)

    if not controle_coherence(res):
        return 1

    resultats = generer_factures(res, Path(args.out), Path(args.compteur),
                                 dry_run=args.dry_run)
    recap_factures(resultats, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
