# Outil de facturation SNG / QUIETIS

CLI Python qui transforme le PDF mensuel « Entrées du mois » (fourni par LIFESTONE)
en factures de commission, **une par société** (QUIETIS GESTION et SNG GROUPE).

```bash
python facture.py entrees_aout_2026.pdf
```

Produit dans `./out/` :

- `Facture_QUIETIS_GESTION_Aout_2026.pdf`
- `Facture_SNG_GROUPE_Aout_2026.pdf`

et incrémente automatiquement la numérotation (`compteur.json`).

## État du projet

> ⚠️ **Dépôt en cours d'initialisation.**
> Les fichiers sources fournis par le prestataire ne sont pas encore déposés
> (voir « Fichiers requis » ci-dessous). Tant qu'ils manquent, le parseur et le
> test de non-régression ne peuvent pas être finalisés.

### Fichiers requis (à déposer à la racine)

| Fichier | Rôle |
|---|---|
| `facture_gen.py` | Moteur de rendu PDF **déjà calibré** — importé tel quel, jamais réécrit. |
| `Facture_SNG_GROUPE_Juin_2026-QUIETIS.pdf` | Modèle de référence pour le test de non-régression. |
| `Facture_SNG_GROUPE_Juin_2026_SFG.pdf` | Modèle. |
| `Entrées_Juillet_2026.pdf` | Échantillon d'entrée pour calibrer le parseur. |

## Architecture cible

- `facture_gen.py` — moteur de rendu (fourni, non modifié). API : `generer(...)`.
- `parser.py` — extraction du PDF « Entrées du mois » via `pdfplumber`.
- `facture.py` — CLI : parsing → contrôle de cohérence → numérotation → rendu.
- `compteur.json` — séquence de numérotation, **continue sur l'année**.
- `tests/` — non-régression PDF + tests unitaires (arrondi, dates, montants, noms).

## Règles métier

1. Base HT par ligne = `TTC / 1,2`, arrondi `ROUND_HALF_UP` à 2 décimales.
2. Total commission HT = somme des bases HT arrondies.
3. Part HT à 50 % = `total_TTC / 1,2 / 2`, arrondie seulement à la fin.
4. TVA = 0 (franchise en base, art. 293 B du CGI).
5. TOTAL À PAYER = Part HT à 50 %.
6. Format monétaire français : espace fine milliers, virgule décimale, `€` suffixe.

Ces règles sont implémentées dans `facture_gen.py` (`ht()`, `eur()`, `r2()`) et ne
sont pas redéveloppées ailleurs.

## Destinataires

| Société (colonne du tableau) | Bloc CLIENT facturé | SIREN |
|---|---|---|
| QUIETIS | QUIETIS GESTION | 810 183 723 |
| SNG | SNG GROUPE | 444 655 955 |

Adresse commune : 1015 Rue du Lieutenant Parayre, CS 40408, 13591 Aix-en-Provence Cedex 3.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Hors périmètre (v1)

Pas d'interface web, pas de base de données, pas d'envoi d'email, pas de déploiement.
