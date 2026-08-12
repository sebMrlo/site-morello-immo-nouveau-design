#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parseur du PDF « Entrées du mois » fourni par LIFESTONE.

Tableau source (sans bordures) :
    Locataire | Résidence | N° lot | Honoraires Locataire | Date d'entrée | Société

Sortie : période détectée (mois/année), lignes normalisées, total imprimé en bas.
Rien n'est « corrigé » silencieusement : chaque normalisation de nom est journalisée
et la vérification finale du total est faite par l'appelant (facture.py).
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import pdfplumber


# ----------------------------------------------------------------- exceptions
class ParserError(Exception):
    """Le PDF source n'a pas pu être interprété (colonnes ou total introuvables)."""


# ----------------------------------------------------------------- mois
_MOIS_PLEIN = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "decembre": 12,
}
_MOIS_ABBR = {
    "janv": 1, "jan": 1, "fevr": 2, "fev": 2, "mars": 3, "mar": 3, "avr": 4,
    "avril": 4, "mai": 5, "juin": 6, "juil": 7, "jui": 7, "aout": 8, "aou": 8,
    "sept": 9, "sep": 9, "oct": 10, "nov": 11, "dec": 12, "decembre": 12,
}

# Affichage (accentué) pour l'objet de la facture.
MOIS_AFFICHE = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre",
    12: "Décembre",
}
# Slug ASCII pour les noms de fichiers.
MOIS_SLUG = {
    1: "Janvier", 2: "Fevrier", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Aout", 9: "Septembre", 10: "Octobre", 11: "Novembre",
    12: "Decembre",
}


# ----------------------------------------------------------------- prénoms
# Gazetteer de prénoms courants. Sert uniquement à identifier le prénom pour en
# déduire le patronyme (le token restant), y compris quand le patronyme est placé
# en premier (ex. « Belkharchouche Malik »). On reste volontairement à l'écart des
# prénoms qui sont aussi des patronymes très courants pour limiter les faux positifs.
GIVEN_NAMES = {
    # prénoms présents dans les données réelles
    "malik", "christophe", "nassim", "ophelie", "noah", "morad", "fathia",
    "mathilde", "anthony",
    # masculins courants
    "alexandre", "alexis", "adam", "adrien", "alain", "albert", "amine", "anis",
    "antoine", "arthur", "aurelien", "axel", "baptiste", "benjamin", "benoit",
    "bilal", "brahim", "bruno", "cedric", "charles", "clement", "corentin",
    "cyril", "damien", "daniel", "david", "dylan", "elias", "emile", "emmanuel",
    "enzo", "eric", "ethan", "fabien", "fabrice", "farid", "florent", "florian",
    "francois", "frederic", "gabriel", "gael", "geoffrey", "georges", "gerard",
    "gilles", "guillaume", "guy", "hamza", "hicham", "hugo", "ibrahim", "ilyes",
    "isaac", "ismael", "jacques", "jean", "jeremy", "jerome", "joel", "jonathan",
    "jordan", "jules", "julien", "kamel", "karim", "kevin", "leo", "lilian",
    "loic", "louis", "lucas", "ludovic", "maël", "mael", "marc", "mathis",
    "mathieu", "matthieu", "maxime", "mehdi", "michel", "mohamed", "mounir",
    "nabil", "nathan", "nicolas", "noe", "olivier", "omar", "pascal", "patrick",
    "paul", "philippe", "pierre", "quentin", "rachid", "raphael", "rayan",
    "remi", "romain", "sacha", "salim", "samir", "samuel", "sebastien", "sofiane",
    "stephane", "sylvain", "theo", "tom", "valentin", "victor", "william", "yanis",
    "yann", "younes", "yassine", "youssef", "zakaria",
    # féminins courants
    "alice", "amandine", "amelie", "anais", "andrea", "anne", "audrey", "aurelie",
    "camille", "carla", "caroline", "catherine", "celia", "celine", "charlene",
    "charlotte", "chloe", "christelle", "christine", "claire", "clara", "clemence",
    "coralie", "delphine", "elisa", "elise", "elodie", "elsa", "emma", "estelle",
    "eva", "fanny", "farida", "fatima", "florence", "gaelle", "ines", "isabelle",
    "jade", "jessica", "julie", "justine", "karima", "laetitia", "latifa", "laura",
    "laure", "laurence", "lea", "leila", "lena", "lina", "lisa", "lise", "louise",
    "lucie", "manon", "margaux", "marie", "marion", "marlene", "melanie", "melissa",
    "morgane", "myriam", "nadia", "nawel", "nina", "noemie", "nora", "oceane",
    "pauline", "rachel", "romane", "sabrina", "salma", "sandra", "sandrine", "sara",
    "sarah", "sofia", "solene", "sonia", "sophie", "stephanie", "sabine", "valerie",
    "vanessa", "victoria", "virginie", "yasmine", "zoe",
}


# ----------------------------------------------------------------- helpers texte
def deaccent(s: str) -> str:
    """Retire les accents pour comparaison insensible (é -> e)."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def _norm_token(s: str) -> str:
    return deaccent(s).lower().strip(" .,:;-'’")


# ----------------------------------------------------------------- montants
_SPACES = "    "


def parse_montant(s: str) -> Decimal:
    """'542,51 €' / '4 831,79 €' -> Decimal('542.51') / Decimal('4831.79')."""
    m = re.search(r"-?\d[\d" + _SPACES + r"]*,\d{2}", s)
    if not m:
        # tolère un montant entier sans décimales
        m = re.search(r"-?\d[\d" + _SPACES + r"]*", s)
        if not m:
            raise ValueError(f"Montant illisible : {s!r}")
    brut = m.group(0)
    for sp in _SPACES:
        brut = brut.replace(sp, "")
    brut = brut.replace(",", ".")
    return Decimal(brut)


# ----------------------------------------------------------------- dates
_DATE_RE = re.compile(
    r"(\d{1,2})\s*[-/\s]\s*([A-Za-zÀ-ÿ]+)\.?\s*[-/\s]\s*(\d{2,4})"
)


def parse_date(s: str) -> str:
    """'03-juil-26' -> '03/07/2026' (mois français abrégés)."""
    m = _DATE_RE.search(s)
    if not m:
        raise ValueError(f"Date illisible : {s!r}")
    jour = int(m.group(1))
    mois_txt = _norm_token(m.group(2))
    if mois_txt not in _MOIS_ABBR and mois_txt not in _MOIS_PLEIN:
        raise ValueError(f"Mois inconnu dans la date : {s!r}")
    mois = _MOIS_ABBR.get(mois_txt) or _MOIS_PLEIN[mois_txt]
    an = int(m.group(3))
    if an < 100:
        an += 2000
    return f"{jour:02d}/{mois:02d}/{an}"


# ----------------------------------------------------------------- noms
_SEP_COUPLE = re.compile(r"\s+et\s+|\s*&\s*|\s+/\s+|\s*\+\s*", re.I)


def _pick_surname(tokens: list[str]) -> tuple[str | None, bool]:
    """Renvoie (patronyme, fiable). patronyme=None si le token est un prénom seul
    (cas d'un membre d'un couple partageant le nom de l'autre)."""
    if len(tokens) == 1:
        if _norm_token(tokens[0]) in GIVEN_NAMES:
            return None, True          # prénom seul -> partage le nom du partenaire
        return tokens[0], True         # patronyme seul
    non_prenoms = [t for t in tokens if _norm_token(t) not in GIVEN_NAMES]
    if len(non_prenoms) == len(tokens):
        # aucun prénom reconnu -> convention française : le nom est en dernier
        return tokens[-1], False
    if non_prenoms:
        # le(s) token(s) qui ne sont pas des prénoms forment le patronyme
        return " ".join(non_prenoms), True
    # tous les tokens sont des prénoms reconnus -> ambigu, on prend le dernier
    return tokens[-1], False


def normalize_nom(raw: str, overrides: dict | None = None) -> tuple[str, bool]:
    """'Belkharchouche Malik Nelya' -> ('BELKHARCHOUCHE', True).
    Renvoie (patronyme(s) en MAJUSCULES, fiable). fiable=False => à vérifier."""
    raw = raw.strip()
    if overrides and raw in overrides:
        return overrides[raw], True
    fiable = True
    surnames: list[str] = []
    last_tokens: list[str] = []
    for part in _SEP_COUPLE.split(raw):
        tokens = [t for t in re.split(r"\s+", part.strip()) if t]
        if not tokens:
            continue
        last_tokens = tokens
        sn, ok = _pick_surname(tokens)
        if not ok:
            fiable = False
        if sn is not None:
            surnames.append(sn)
    # dédoublonnage en préservant l'ordre (insensible à la casse/accents)
    seen, uniq = set(), []
    for s in surnames:
        k = _norm_token(s)
        if k and k not in seen:
            seen.add(k)
            uniq.append(s)
    if not uniq:
        uniq = [last_tokens[-1]] if last_tokens else [raw]
        fiable = False
    result = "-".join(u.upper() for u in uniq)
    return result, fiable


# ----------------------------------------------------------------- structures
@dataclass
class Entree:
    date: str            # jj/mm/aaaa
    nom_raw: str         # libellé source
    nom: str             # patronyme(s) normalisés MAJUSCULES
    residence: str       # MAJUSCULES
    lot: str
    ttc: Decimal
    societe: str         # QUIETIS / SNG (MAJUSCULES)
    nom_fiable: bool = True


@dataclass
class ParseResult:
    mois: int
    annee: int
    entrees: list[Entree]
    total_source: Decimal
    avertissements: list[str] = field(default_factory=list)

    @property
    def total_extrait(self) -> Decimal:
        from decimal import ROUND_HALF_UP
        s = sum((e.ttc for e in self.entrees), Decimal("0"))
        return s.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ----------------------------------------------------------------- extraction
_COL_KEYS = ["locataire", "residence", "lot", "honoraires", "date", "societe"]


def _detect_periode(words) -> tuple[int, int]:
    """Trouve le mois plein (« Juillet ») et l'année (« 2026 ») dans l'en-tête."""
    mois = None
    for w in words:
        t = _norm_token(w["text"])
        if t in _MOIS_PLEIN:
            mois = _MOIS_PLEIN[t]
            break
    annees = [w for w in words if re.fullmatch(r"20\d{2}", w["text"].strip())]
    annee = int(annees[0]["text"]) if annees else None
    if mois is None or annee is None:
        raise ParserError(
            f"Période introuvable dans l'en-tête (mois={mois}, année={annee})."
        )
    return mois, annee


def _column_separators(header_words) -> list[float]:
    """Calcule les 5 bornes verticales séparant les 6 colonnes, à partir des
    positions x0 des libellés d'en-tête distinctifs."""
    x = {}

    def put(key, w):
        if key not in x or w["x0"] < x[key]:
            x[key] = w["x0"]

    for w in header_words:
        t = _norm_token(w["text"])
        if t == "locataire":
            put("locataire", w)      # 1re occurrence = colonne Locataire
        elif t == "residence":
            put("residence", w)
        elif t in ("n", "n°", "lot"):
            put("lot", w)
        elif t.startswith("honoraires"):
            put("honoraires", w)
        elif t == "date":
            put("date", w)
        elif t == "societe":
            put("societe", w)
    manquants = [k for k in _COL_KEYS if k not in x]
    if manquants:
        raise ParserError(f"Colonnes introuvables dans l'en-tête : {manquants}")
    # séparateurs = bords gauches des colonnes 2..6
    seps = sorted([x["residence"], x["lot"], x["honoraires"], x["date"], x["societe"]])
    return seps


def _bucket(cx: float, seps: list[float]) -> int:
    for i, s in enumerate(seps):
        if cx < s:
            return i
    return len(seps)  # dernière colonne (societe)


def _cluster_lines(words, tol=3.5):
    """Regroupe les mots en lignes selon leur position verticale."""
    lines = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        placed = False
        for ln in lines:
            if abs(ln["top"] - w["top"]) <= tol:
                ln["words"].append(w)
                ln["top"] = (ln["top"] * ln["n"] + w["top"]) / (ln["n"] + 1)
                ln["n"] += 1
                placed = True
                break
        if not placed:
            lines.append({"top": w["top"], "n": 1, "words": [w]})
    for ln in lines:
        ln["words"].sort(key=lambda w: w["x0"])
    lines.sort(key=lambda ln: ln["top"])
    return lines


def _cells(line_words, seps) -> list[str]:
    cols = ["" for _ in range(6)]
    for w in line_words:
        cx = (w["x0"] + w["x1"]) / 2
        i = _bucket(cx, seps)
        cols[i] = (cols[i] + " " + w["text"]).strip()
    return cols


def parse_entrees(pdf_path: str | Path, overrides: dict | None = None) -> ParseResult:
    """Extrait période, lignes et total imprimé du PDF « Entrées du mois »."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(path)

    with pdfplumber.open(str(path)) as pdf:
        page = pdf.pages[0]
        words = page.extract_words(use_text_flow=False, keep_blank_chars=False)

    mois, annee = _detect_periode(words)

    # ligne d'en-tête = celle qui contient « Société »
    soc = [w for w in words if _norm_token(w["text"]) == "societe"]
    if not soc:
        raise ParserError("En-tête du tableau introuvable (« Société » absent).")
    hdr_top = min(w["top"] for w in soc)
    header_words = [w for w in words if abs(w["top"] - hdr_top) <= 4.0]
    hdr_bottom = max(w["bottom"] for w in header_words)
    seps = _column_separators(header_words)

    body = [w for w in words if w["top"] > hdr_bottom + 1.0]
    lines = _cluster_lines(body)

    entrees: list[Entree] = []
    avertissements: list[str] = []
    total_source: Decimal | None = None

    for ln in lines:
        cells = _cells(ln["words"], seps)
        locataire, residence, lot, honos, date_c, societe = cells
        soc_norm = _norm_token(societe)

        est_ligne = bool(locataire) and soc_norm.isalpha() and soc_norm != ""
        if est_ligne:
            try:
                ttc = parse_montant(honos)
                date_fr = parse_date(date_c)
            except ValueError as exc:
                avertissements.append(f"Ligne ignorée (illisible) : {cells} — {exc}")
                continue
            nom, fiable = normalize_nom(locataire, overrides)
            entrees.append(Entree(
                date=date_fr,
                nom_raw=locataire,
                nom=nom,
                residence=residence.upper(),
                lot=lot.strip(),
                ttc=ttc,
                societe=soc_norm.upper(),
                nom_fiable=fiable,
            ))
        else:
            # ligne sans société : candidate « total imprimé » si elle porte un montant
            joined = " ".join(cells)
            if re.search(r"\d,\d{2}", joined):
                try:
                    total_source = parse_montant(joined)
                except ValueError:
                    pass

    if not entrees:
        raise ParserError("Aucune ligne d'entrée détectée dans le tableau.")
    if total_source is None:
        raise ParserError("Total imprimé introuvable en bas du PDF source.")

    return ParseResult(mois, annee, entrees, total_source, avertissements)


def load_overrides(path: str | Path) -> dict:
    """Charge un fichier optionnel de corrections manuelles de noms (raw -> NORMALISÉ)."""
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))
