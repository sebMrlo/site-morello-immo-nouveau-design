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

## Architecture

- `facture_gen.py` — moteur de rendu PDF **fourni, non modifié**. API : `generer(...)`.
- `parser.py` — extraction du PDF « Entrées du mois » via `pdfplumber`
  (période, lignes, total imprimé) + normalisation dates/montants/noms.
- `facture.py` — CLI : parsing → contrôle de cohérence → numérotation → rendu.
- `compteur.json` — séquence de numérotation, **continue sur l'année**.
- `noms_overrides.json` *(optionnel)* — corrections manuelles de noms (`libellé source` → `NORMALISÉ`).
- `tests/` — non-régression PDF au 0,1 pt + tests unitaires (arrondi, dates, montants, noms, CLI).

## Utilisation

```bash
python facture.py Entrées_Aout_2026.pdf          # génère les factures dans ./out/
python facture.py Entrées_Aout_2026.pdf --dry-run  # analyse + contrôle, sans rien écrire
```

Options : `--out` (dossier de sortie), `--compteur` (fichier de numérotation),
`--overrides` (corrections de noms).

Le CLI affiche systématiquement :
1. la période détectée et le nombre de lignes ;
2. **la table des noms normalisés** (chaque `libellé source → PATRONYME`, les cas
   incertains marqués `⚠`) — à vérifier, la normalisation étant heuristique ;
3. le **contrôle de cohérence** : somme des honoraires extraits vs total imprimé
   sur le PDF source. En cas d'écart, il affiche le montant et **s'arrête sans
   rien générer** (garde-fou principal) ;
4. le récapitulatif par société (lignes, TTC, HT, part 50 %, n° de facture, fichier).

### Normalisation des noms

Heuristique : on isole le **patronyme** de chaque locataire (prénom retiré via un
petit dictionnaire de prénoms), couples séparés sur « et »/« & » et patronymes
joints par un tiret (`RODRIGUES-JADOT`). Le cas patronyme-en-premier
(`Belkharchouche Malik → BELKHARCHOUCHE`) est géré. Tout résultat incertain est
signalé `⚠` dans la console ; un `noms_overrides.json` permet de figer une
correction :

```json
{ "Libellé exact du PDF source": "PATRONYME_CORRIGÉ" }
```

## Tests

```bash
python -m pytest tests/ -q
```

Le test de non-régression (`tests/test_regression.py`) régénère la facture QUIETIS
de juillet 2026 et compare la position de **chaque mot** au PDF de référence
`tests/golden/Facture_QUIETIS_Juillet_2026.pdf` **au 0,1 pt près**. Ce golden a
été produit par `facture_gen.py` ; ses valeurs chiffrées sont identiques, au
centime, à la facture réelle F‑2026‑07‑001. Pour l'ancrer sur le vrai PDF de juin,
il suffit de remplacer le golden par le fichier d'origine et d'ajuster
`tests/reference.py`.

> Note : `tests/fixtures/entrees_juillet_2026.pdf` est une **reconstitution**
> synthétique du document LIFESTONE (mêmes colonnes, mêmes données réelles de
> juillet), générée par `tests/make_fixture.py`. À la première utilisation sur un
> vrai PDF LIFESTONE, vérifier le récapitulatif de cohérence ; le garde-fou du
> total rend toute ligne manquée bruyante.

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
