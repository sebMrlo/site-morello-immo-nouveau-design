#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère un PDF « Entrées du mois » synthétique reproduisant la mise en page
(colonnes sans bordures) du document LIFESTONE, à partir des données réelles de
Juillet 2026 (extraites de la facture F-2026-07-001/002). Sert de fixture aux tests.

Ce n'est PAS le vrai PDF LIFESTONE : c'est une reconstitution fidèle de sa
structure de colonnes, suffisante pour valider le parseur géométrique de bout en bout.
"""
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

_FONT = "DejaVu"
_BOLD = "DejaVu-Bold"
try:
    pdfmetrics.registerFont(TTFont(_FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont(_BOLD, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
except Exception:  # déjà enregistrées via facture_gen
    pass

PW, PH = 595.2756, 841.8898

# Bornes gauches (x0) des colonnes — largement séparées, colonne Locataire large.
X = {
    "locataire": 40,
    "residence": 215,
    "lot": 300,
    "honoraires": 350,   # montants alignés à droite sur X_HONO_R
    "date": 450,
    "societe": 525,
}
X_HONO_R = 430  # bord droit d'alignement des montants

JUILLET_2026 = [
    ("Belkharchouche Malik", "Nelya", "A202", "542,51 €", "03-juil-26", "Quietis"),
    ("Mathilde Rodrigues et Anthony Jadot", "Nelya", "B103", "690,00 €", "07-juil-26", "Quietis"),
    ("Christophe Andre", "Rue Dorée", "2E", "630,28 €", "07-juil-26", "Quietis"),
    ("Nassim Diafi", "Rue Colbert", "1", "450,00 €", "13-juil-26", "SNG"),
    ("Ophélie Serbon", "Nelya", "B202", "850,00 €", "17-juil-26", "Quietis"),
    ("Morad et fathia Remmach", "Althea", "B108", "899,00 €", "21-juil-26", "Quietis"),
    ("Noah Angonnet", "Nelya", "B006", "770,00 €", "21-juil-26", "Quietis"),
]
TOTAL = "4 831,79 €"


def make(path, rows=JUILLET_2026, total=TOTAL, mois="Juillet", annee="2026"):
    c = canvas.Canvas(str(path), pagesize=(PW, PH))

    # bloc adresse / en-tête
    c.setFont(_BOLD, 8)
    c.drawString(50, PH - 55, "NOM Prénom")
    c.drawString(50, PH - 67, "Domicile")
    c.setFont(_FONT, 8)
    c.drawString(230, PH - 55, "MORELLO")
    c.drawString(360, PH - 55, "Sébastien")
    c.drawString(230, PH - 67, "345 Rue du jeu de mail des abbés 340000 Montpellier")
    c.setFont(_BOLD, 8)
    c.drawString(430, PH - 100, "LIFESTONE")
    c.setFont(_FONT, 8)
    c.drawString(430, PH - 112, "1015 Rue du Lieutenant parayre")
    c.drawString(430, PH - 124, "13591 aix en provence cedex 3")
    c.drawString(430, PH - 136, "cs 40408")

    # période
    c.setFont(_BOLD, 8)
    c.drawString(360, PH - 168, "Mois :")
    c.drawString(470, PH - 168, "Année :")
    c.setFont(_FONT, 8)
    c.drawString(378, PH - 182, mois)
    c.drawString(488, PH - 182, annee)

    # en-tête du tableau (libellés en une seule chaîne par colonne : les espaces
    # réels garantissent une segmentation propre des mots par pdfplumber)
    y = PH - 208
    c.setFont(_BOLD, 7)
    c.drawString(X["locataire"], y, "Locataire")
    c.drawString(X["residence"], y, "Résidence")
    c.drawString(X["lot"], y, "N° lot")
    c.drawString(X["honoraires"], y, "Honoraires Locataire")
    c.drawString(X["date"], y, "Date d'entrée")
    c.drawString(X["societe"], y, "Société")

    # corps
    c.setFont(_FONT, 7)
    ry = y - 18
    for nom, res, lot, hono, date, soc in rows:
        c.drawString(X["locataire"] + 5, ry, nom)
        c.drawString(X["residence"], ry, res)
        c.drawString(X["lot"], ry, lot)
        c.drawRightString(X_HONO_R, ry, hono)
        c.drawString(X["date"], ry, date)
        c.drawString(X["societe"], ry, soc)
        ry -= 17

    # total imprimé (seul, aligné comme les montants)
    ry -= 18
    c.drawRightString(X_HONO_R, ry, total)

    c.save()
    return path


if __name__ == "__main__":
    out = Path(__file__).parent / "fixtures" / "entrees_juillet_2026.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    make(out)
    print("écrit :", out)
