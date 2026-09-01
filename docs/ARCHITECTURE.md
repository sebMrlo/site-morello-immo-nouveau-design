# Proposition d'architecture — SaaS de facturation « prêt facturation électronique »

> **Statut : proposition à valider.** Conformément à la section 47 du cahier des
> charges, ce document analyse le besoin, propose l'architecture et liste les
> décisions à prendre. **Aucune implémentation ne démarre avant validation.**

## 0. Avertissement réglementaire (à lire en premier)

Ce document ne certifie **aucune** conformité. Il est écrit avec une date de
connaissance arrêtée à **janvier 2026** ; les spécifications de la réforme
française évoluent (le porteur du projet cite une v3.2 au 2 juillet 2026 et les
normes XP Z12‑012/013/014). **Toute affirmation réglementaire datée doit être
vérifiée** sur les sources officielles (impots.gouv.fr / DGFiP, AFNOR pour les
normes XP) **et avec un expert‑comptable** avant toute mise en production.

La parade architecturale à cette incertitude est simple et structurante : **on ne
code jamais un format ou une plateforme « en dur »**. Tout passe par un modèle
interne (`CanonicalInvoice`) et des **adaptateurs** remplaçables. Si un format ou
une API change, on remplace un adaptateur, pas l'application.

### Le point de positionnement (validé, c'est la bonne lecture)

| | Notre logiciel | Plateforme agréée (PDP) |
|---|---|---|
| Nature | Solution de facturation / « solution compatible » | Intermédiaire **immatriculé** par l'administration |
| Fait | UX, saisie, PDF, suivi, **préparation** des données structurées | Transmission, réception, e‑reporting, interopérabilité inter‑plateformes, échanges avec l'administration |
| Ne fait pas | Les fonctions réservées à une PDP | — |

Conséquence : notre produit **s'interface** avec une ou plusieurs PDP. Il ne se
présente jamais comme « certifié par l'État » / « agréé DGFiP ». La signalétique
« solution compatible » n'est utilisée que si une procédure officielle nous y
autorise réellement.

---

## 1. Principe directeur : `CanonicalInvoice` au centre

```
                       ┌───────────────────────────┐
        saisie  ─────► │      Domaine métier       │
        (UI/API)       │  Invoice / Customer / ...  │
                       └─────────────┬──────────────┘
                                     │ mappe vers
                             ┌───────▼────────┐
                             │ CanonicalInvoice│  ← modèle pivot, indépendant
                             └───┬────────┬────┘     du PDF, de la DB et de la PDP
                    ┌────────────┘        └────────────┐
             ┌──────▼──────┐                    ┌───────▼────────┐
             │  Rendu PDF  │                    │ ProviderAdapter │
             │ (facture_gen│                    │  (port unique)  │
             │  + Factur-X)│                    └───────┬────────┘
             └─────────────┘             ┌──────────────┼──────────────┐
                                    ┌─────▼────┐   ┌─────▼────┐   ┌─────▼────┐
                                    │ PDP A    │   │ PDP B    │   │ PDP C    │
                                    └──────────┘   └──────────┘   └──────────┘
```

`CanonicalInvoice` est **la** source de vérité métier. Le PDF n'en est qu'une
représentation. La persistance (Mongo ou Postgres) n'en est qu'un stockage. La
PDP n'en est qu'un canal. C'est l'exigence architecturale majeure (section 18).

---

## 2. Continuité avec l'existant (ne rien jeter)

L'atout déjà en place s'insère proprement dans ce schéma :

- `facture_gen.py` devient **un** moteur de rendu derrière « Rendu PDF ». Il reste
  intact ; le `CanonicalInvoice` produit le tuple d'entrées qu'il attend.
- Les règles métier déjà écrites et **testées** (base HT = TTC/1,2 `ROUND_HALF_UP`,
  part 50 %, format monétaire FR, numérotation continue, garde‑fou de cohérence)
  sont le **noyau du domaine**. On les remonte du CLI vers le service métier ; on
  ne les réécrit pas.
- Le parseur `pdfplumber` reste utile comme **connecteur d'import** (charger des
  lots d'entrées LIFESTONE), pas comme cœur du produit.

Autrement dit, le CLI actuel est le **Phase 0** déjà livré et vert.

---

## 3. Modèle de données (aperçu)

Entités (rattachées à `organization_id`, cf. §7) :

- `Organization`, `Establishment` — émetteur, multi‑établissement.
- `Customer` — particulier / pro / entreprise, identifiants d'adressage B2B.
- `Quote` → `Invoice` (conversion sans ressaisie), `CreditNote`.
- `Invoice` avec `InvoiceLine[]` : montants, TVA multi‑taux, remises, échéance,
  mentions ; **statut** (machine à états §5) ; référence de numérotation.
- `Payment` (partiel/multiple), soldes calculés.
- `InvoiceEvent` / `AuditLog` — **journal immuable** (§5, §20).
- `ElectronicTransmission` — état d'envoi PDP, `idempotency_key`, corrélation.
- `ProviderConnection` — secrets PDP (**backend uniquement**, chiffrés).
- `Subscription` / `Plan` / `Limits` — SaaS commercial (non figé dans le code).

`CanonicalInvoice` est un modèle **dérivé** (Pydantic) construit depuis `Invoice`,
volontairement séparé du modèle de persistance.

---

## 4. Machine à états (pas de simple draft/sent/paid)

```
DRAFT → VALIDATED → GENERATED → SUBMITTED → ACCEPTED → DELIVERED → PAID
                                     │            │
                                     ├─► REJECTED │
                                     └─► TRANSMISSION_ERROR
   (parallèle paiement) : UNPAID / PARTIALLY_PAID / PAID / OVERDUE
   sortie : CANCELLED (via avoir/rectificative, jamais suppression)
```

Chaque transition est **validée** (transitions autorisées seulement) et
**journalisée** (qui, quand, ancienne/nouvelle valeur, IP, user‑agent). Après
`VALIDATED`, les données fiscales sont **verrouillées** : correction = avoir ou
facture rectificative, jamais modification/suppression silencieuse (§12).

---

## 5. Numérotation : exigence transactionnelle (point sensible)

Le test cible (section 36) : *deux utilisateurs créent une facture en même temps →
deux numéros différents, aucune réutilisation, aucune suppression d'un numéro
émis*. C'est un problème de **concurrence**, pas de formatage.

- Séquence par `(organization_id, exercice, préfixe)`, format configurable
  (`2026-000001`).
- L'attribution du numéro se fait **au moment de `VALIDATED`** (pas au brouillon),
  dans une **transaction** avec verrou.
  - **Postgres** : `SEQUENCE` dédiée ou table compteur avec `SELECT … FOR UPDATE` /
    contrainte `UNIQUE (org, exercice, numero)` — garanties natives et testables.
  - **MongoDB** : `findOneAndUpdate($inc)` atomique + index `unique` — faisable,
    mais les garanties transactionnelles multi‑documents sont plus délicates.

Ce besoin (numérotation + immuabilité + audit + isolation) est l'argument
principal du **point de décision base de données** (§9).

---

## 6. Multi‑tenant & isolation

`USER → ORGANIZATION → ESTABLISHMENT → CUSTOMERS/INVOICES/PAYMENTS`. Règle
absolue : impossible d'accéder à une ressource d'une autre organisation **même en
connaissant son ID**. Deux couches :

1. **Applicative** : chaque requête filtre par `organization_id` issu du token ;
   jamais depuis un paramètre client.
2. **Base** : idéalement **Row‑Level Security** (Postgres) pour une isolation
   défendable en profondeur ; en Mongo, discriminant obligatoire + tests dédiés.

RBAC : `owner` / `admin` / `user`, extensible. Un admin **SaaS** (technique) n'a
pas automatiquement accès au **contenu** des factures (§35) — séparation
droits techniques / droits métier.

---

## 7. ProviderAdapter (port & adaptateurs)

Interface unique (port), adaptateurs interchangeables. **Aucun endpoint PDP n'est
écrit avant d'avoir la doc officielle du partenaire choisi** (§42).

```
ElectronicInvoicingProvider (port)
  authenticate() · submit_invoice() · submit_credit_note()
  get_invoice_status() · receive_invoice() · get_directory_data()
  submit_payment_data() · cancel_submission() · handle_webhook()
```

Transmissions **idempotentes** (`idempotency_key`), webhooks **authentifiés,
idempotents, rejouables, journalisés** (§32‑33).

---

## 8. Moteur de conformité `InvoiceComplianceEngine`

Service indépendant, appelé avant `VALIDATED`. Retourne des erreurs
**structurées et compréhensibles** :

```json
{ "valid": false,
  "errors": [ { "field": "customer.siret", "code": "MISSING_SIRET",
                "message": "Le SIRET du client est requis pour une facture B2B." } ] }
```

Contrôles : identité vendeur/client, SIREN/SIRET, numéro, dates, lignes,
montants, TVA, **cohérence mathématique des totaux**, mentions obligatoires,
données nécessaires à l'échange électronique. Les **règles** sont versionnées et
tracées dans `COMPLIANCE_MATRIX.md` (preuve documentaire, §44).

---

## 9. Stack & décisions

Le cahier des charges fixe **React/TS + FastAPI + MongoDB Atlas + Vercel/Render**.
Je propose de **conserver front/back tels quels** et de **rouvrir un seul point** :

> **Décision D1 — Base de données.** Les exigences dominantes du produit
> (numérotation concurrente sûre, immuabilité, piste d'audit, isolation tenant
> défendable) sont le terrain de prédilection d'un **SGBD relationnel
> transactionnel**. Je recommande **PostgreSQL** (séquences, `FOR UPDATE`,
> contraintes `UNIQUE`, RLS) plutôt que MongoDB. À noter : cet environnement
> dispose déjà d'un connecteur **Supabase (Postgres)** ; il n'y a **pas** de
> connecteur MongoDB ici. MongoDB reste faisable, mais nous porterions
> nous‑mêmes des garanties que Postgres offre nativement.
> *À trancher par toi — je ne change pas la stack sans ta validation (§4 du CDC).*

Reste inchangé : FastAPI + Pydantic (services/repositories/adapters séparés,
jamais de logique métier dans les routes), React/TS/Vite/Tailwind, Brevo pour
l'email, stockage objet pour les documents.

---

## 10. Sécurité & RGPD (socle)

HTTPS, auth sécurisée (hash mots de passe, refresh tokens, MFA ultérieure), RBAC,
rate limiting, validation **backend** systématique, isolation tenant, secrets PDP
**jamais** côté frontend, logs/audit, sauvegardes, rotation des secrets.
RGPD : minimisation, export, conservation, séparation par organisation, base
prête pour DPA/registre/demandes.

---

## 11. Incohérences & risques relevés (l'analyse demandée §47.2/47.3/47.12)

1. **Périmètre vs « MVP simple » (§40) contre l'ampleur (§1‑39).** Le CDC liste un
   produit très riche tout en exigeant de ne pas sur‑développer. Risque : dispersion.
   → *Reco : figer un MVP étroit (Phase 1‑3) et tenir les sections avancées comme
   « architecture prête, non développée ».*
2. **MongoDB vs exigences transactionnelles** (§5, §9) → décision D1.
3. **Dépendance réglementaire externe.** Formats/normes/dates non certifiables ici
   → conception agnostique + `COMPLIANCE_MATRIX.md` comme garde‑fou.
4. **Choix de la PDP = décision produit ET commerciale** (coût/facture, sandbox,
   webhooks, marque blanche). Elle **conditionne** l'adaptateur et une partie du
   modèle économique. Ne pas coder le connecteur avant ce choix (§42).
5. **Emplacement du code.** Ce dépôt est `site-morello-immo-nouveau-design`
   (site + outil CLI). Un SaaS mérite probablement **son propre dépôt** → décision D2.
6. **Positionnement légal des mentions** (« compatible » vs « certifié »).
   → jamais de revendication non acquise ; textes marketing validés en amont.
7. **Coût/temps.** C'est un produit de plusieurs mois. Le rythme par phases (§41)
   est la bonne réponse ; chaque phase = livrable testé avant la suivante.

---

## 12. Plan par phases (aligné §41, ancré sur l'existant)

| Phase | Contenu | État |
|---|---|---|
| **0** | Moteur PDF calibré + règles métier + CLI + tests | ✅ **livré** |
| 1 | Architecture (ce doc) + schéma DB + auth + squelette back/front | proposé |
| 2 | Organisations + établissements + clients (+ isolation tenant) | à venir |
| 3 | Devis + factures + avoirs (domaine + numérotation transactionnelle) | à venir |
| 4 | PDF (réutilise `facture_gen`) + emails (Brevo) | à venir |
| 5 | Paiements + relances | à venir |
| 6 | Audit + sécurité + machine à états | à venir |
| 7 | `CanonicalInvoice` + `InvoiceComplianceEngine` + Factur‑X | à venir |
| 8 | `ElectronicInvoicingProvider` (port + tests, sans PDP réelle) | à venir |
| 9 | Connexion à **une** PDP choisie (doc officielle en main) | à venir |
| 10 | Tests complets + préparation commercialisation | à venir |

Chaque phase : expliquer → développer → tester → corriger → vérifier
non‑régression → phase suivante.

---

## 13. Décisions requises avant d'implémenter la Phase 1

- **D1 — Base de données** : PostgreSQL (recommandé) ou MongoDB Atlas (CDC) ?
- **D2 — Dépôt** : nouveau dépôt dédié au SaaS, ou continuer dans celui‑ci ?
- **D3 — Point d'attaque Phase 1** : (a) ce document seul et on s'arrête pour
  validation, ou (b) je peux enchaîner sur le **schéma de base + squelette
  back/front** une fois D1/D2 tranchés.

Rien n'est supprimé du cahier des charges ; les sections avancées sont
« architecture prête, développement différé » et non abandonnées.
