# Revue de conformité — regard « expert‑comptable » sur `ARCHITECTURE.md`

> **Nature et limites de ce document.** Rédigé par un assistant IA, **pas par un
> expert‑comptable inscrit à l'Ordre**. Il ne constitue **ni un conseil comptable,
> ni un conseil juridique ou fiscal, ni une attestation de conformité**. Il vise à
> **outiller la discussion avec un expert‑comptable en exercice**. Date de
> connaissance : **janvier 2026** ; plusieurs paramètres (dates d'entrée en
> vigueur, seuils de franchise, version des spécifications externes) ont évolué
> récemment et sont marqués **« à confirmer »**. Sources à recouper :
> impots.gouv.fr / DGFiP, Légifrance (textes cités), AFNOR (normes XP), et un
> professionnel du chiffre.

---

## 1. Verdict de synthèse

Sur le plan réglementaire, `ARCHITECTURE.md` est **sain dans ses fondations** :

- la distinction **solution de facturation ≠ plateforme agréée (PDP)** est
  **correcte** et bien posée ;
- le refus d'auto‑certification et l'interdiction d'inventer une conformité sont
  **conformes à la prudence attendue** ;
- l'approche **agnostique au format/plateforme** (`CanonicalInvoice` + adaptateurs)
  est **la bonne parade** à l'instabilité réglementaire ;
- l'**immuabilité + avoir/rectificative + piste d'audit** est **alignée** avec les
  exigences fiscales de tenue des factures.

Mais le document raisonne surtout en **architecte logiciel**. Un expert‑comptable
y ajouterait plusieurs **exigences fiscales concrètes** aujourd'hui absentes
(section 4 ci‑dessous) et corrigerait quelques **imprécisions** (section 3). Le
document reste une **proposition** : ces compléments doivent l'enrichir avant tout
développement.

---

## 2. Ce que le document dit juste (validé)

| Point du doc | Appréciation |
|---|---|
| PDP = seul intermédiaire habilité à transmettre / e‑reporter | ✔ correct |
| PPF recentré sur annuaire + concentrateur (fin du dépôt gratuit annoncée fin 2024) | ✔ correct (à re‑confirmer, sujet mouvant) |
| Formats du socle : Factur‑X / UBL / CII (base EN 16931) | ✔ correct |
| Immuabilité d'une facture émise ; correction par avoir | ✔ conforme aux principes fiscaux |
| Numérotation chronologique, continue, sans rupture | ✔ conforme (art. 242 nonies A ann. II CGI, *à confirmer*) |
| Franchise en base = **concernée** par la réforme | ✔ correct (assujetti non redevable) |
| Ne pas revendiquer « certifié État » sans procédure | ✔ prudence justifiée |

---

## 3. Points à corriger ou préciser dans le document

1. **Mention de franchise — formulation.** Le moteur actuel écrit
   « *TVA : Franchise en base - article 293 B du CGI* ». La formule fiscale
   attendue est **« TVA non applicable, article 293 B du CGI »**. À aligner
   (mention obligatoire, art. 293 B CGI — *à confirmer avec l'EC*).

2. **Deux régimes de « conformité logicielle » distincts — ne pas les confondre.**
   Le document (et la question initiale « validée par le gouvernement ») mélange
   potentiellement :
   - la **réforme e‑invoicing** (passage par une **PDP**), et
   - la **loi anti‑fraude TVA** (art. 286‑I‑3° bis CGI) qui impose un **logiciel de
     caisse/gestion certifié** (attestation éditeur ou NF525) **pour les
     encaissements B2C**.
   Ce sont **deux obligations différentes**. Pour un usage **B2B** pur, la
   certification « logiciel de caisse » **ne s'applique en principe pas** ; mais si
   le SaaS enregistre un jour des **encaissements de particuliers**, elle peut
   entrer en jeu. À trancher explicitement dans la matrice.

3. **Base légale à citer.** La matrice gagnerait à référencer les textes fondateurs
   (à confirmer versions à jour) : **ordonnance n° 2021‑1190 du 15/09/2021**, sa
   ratification/aménagements en **loi de finances 2024 (art. 91)**, et les décrets
   d'application, plutôt que les seules normes XP Z12‑012/013/014.

4. **Calendrier — ne pas le laisser implicite.** Le doc renvoie « à vérifier », ce
   qui est prudent, mais l'EC voudra le figer noir sur blanc (section 5).

---

## 4. Angles réglementaires **manquants** (ce qu'un EC ajouterait)

Ces éléments ne figurent pas dans `ARCHITECTURE.md` et devraient enrichir le
`InvoiceComplianceEngine` et la `COMPLIANCE_MATRIX` :

1. **Les 4 nouvelles mentions obligatoires** apportées par la réforme (en plus des
   mentions classiques du CGI), *à confirmer* :
   - **numéro SIREN du client** ;
   - **adresse de livraison** des biens si différente de l'adresse de facturation ;
   - **nature de l'opération** : livraison de biens / prestation de services / mixte ;
   - mention de l'**option pour le paiement de la TVA d'après les débits**, le cas échéant.
   → Ton activité (états des lieux) = **prestation de services** : la nature
   « service » devra être portée correctement.

2. **Mapping TVA pour la franchise en base (technique mais critique).** En
   Factur‑X / EN 16931, une opération en franchise se code généralement en
   **catégorie de TVA « E » (exonéré/exempté)** avec un **motif d'exonération**
   (texte/He code renvoyant à l'art. 293 B). Un taux « 0 % » naïf serait
   **non conforme**. C'est un point que le moteur de conformité doit gérer
   explicitement. *(à confirmer sur les spécifications à jour)*

3. **e‑reporting — distinct de l'e‑invoicing.** Le doc ne le traite pas :
   - **B2B domestique** (tes factures à SNG/QUIETIS) → **e‑invoicing** via PDP ;
   - **B2C** (si tu factures des particuliers) → **e‑reporting** des données de transaction ;
   - opérations avec des **assujettis étrangers** → e‑reporting ;
   - **données d'encaissement** pour les **prestations de services** → e‑reporting
     de paiement (car la TVA des services est en principe exigible à
     l'encaissement). **Cas particulier franchise** : sans TVA due, l'étendue de
     cette obligation mérite une **confirmation expresse de l'EC**.

4. **Archivage & valeur probante.** À intégrer : **conservation 10 ans** des
   factures (obligation comptable, art. L123‑22 C. com.), et exigences de **piste
   d'audit fiable / valeur probante** (art. 289 VII CGI) selon le mode d'émission.
   Le doc parle d'« archivage » sans ces échéances/obligations.

5. **Continuité de numérotation & séries.** Préciser : numérotation **chronologique
   et continue**, remise à zéro par exercice **admise uniquement** via une **série
   distincte** (préfixe) ; interdiction de trou/réutilisation. Le compteur actuel
   (continu sur l'année) est conforme ; à documenter comme règle fiscale, pas
   seulement technique.

6. **Avoirs / factures rectificatives.** Bien prévus dans l'archi ; l'EC voudra les
   **mentions spécifiques** de l'avoir (référence à la facture d'origine, motif).

---

## 5. Analyse **spécifique à ta situation** (EI, franchise 293 B, EDL pour SNG/QUIETIS)

**Ton périmètre.** Tu factures des **entreprises** (SNG, QUIETIS) des **prestations
de services** (états des lieux) en **B2B domestique** → tu es **pleinement dans le
champ de l'e‑invoicing** pour ces factures.

**Ton calendrier (à confirmer, cadre post‑LF 2024) :**

| Obligation | Qui | Échéance *(à confirmer)* |
|---|---|---|
| **Recevoir** des factures électroniques | toutes les entreprises | **1er sept. 2026** (donc *déjà en vigueur* à la date d'aujourd'hui) |
| **Émettre** en électronique | **TPE / micro** (ton cas) | **1er sept. 2027** |

→ **Aujourd'hui**, ton obligation active est la **réception** (via une PDP). Tu as
~1 an avant l'**émission** obligatoire. Confirme ta **catégorie de taille**
(micro/TPE) avec l'EC : c'est elle qui fixe la date d'émission.

**Franchise en base — deux vigilances :**
- mention exacte **« TVA non applicable, article 293 B du CGI »** ;
- **seuils de franchise** : ils ont fait l'objet de **modifications et de débats
  récents** (loi de finances 2025 et suites). Un franchissement de seuil te ferait
  **sortir de la franchise** → TVA à facturer, mentions différentes. **À vérifier
  avec l'EC** : je ne peux pas garantir les seuils applicables à ta date.

**Conseil d'EC, honnête et important — distinguer deux besoins :**
1. **Ta conformité personnelle** (obligation légale) : pour un volume de quelques
   factures/mois, le chemin le plus sûr et le moins cher est de **souscrire à une
   PDP** (interfaces simples, offres TPE) — **pas** de développer un logiciel.
2. **Ton ambition produit** (le SaaS) : c'est un **projet d'entreprise** distinct de
   ta conformité. Légitime, mais ne le confonds pas avec « me mettre en règle ».

Si l'objectif immédiat est « être en règle », la réponse d'un EC serait
probablement : **choisis une PDP et branche‑toi**. Si l'objectif est « créer un
produit à vendre », alors l'architecture proposée est le bon cadre — en gardant la
PDP comme **partenaire**, jamais comme une brique à réimplémenter.

---

## 6. Compléments recommandés pour `COMPLIANCE_MATRIX.md`

Ajouter des lignes avec **référence légale** et **preuve** :

- Ordonnance 2021‑1190 ; LF 2024 art. 91 ; décrets d'application *(versions à jour)*.
- 4 nouvelles mentions obligatoires (chacune une ligne).
- Mapping TVA franchise (catégorie « E » + motif d'exonération).
- e‑reporting (B2C / étranger / encaissements services) — applicabilité au cas franchise.
- Conservation 10 ans (L123‑22 C. com.) + PAF (289 VII CGI).
- Distinction loi anti‑fraude caisse (286‑I‑3° bis CGI) vs e‑invoicing.
- Mention exacte franchise 293 B.

---

## 7. Questions précises à poser à un expert‑comptable en exercice

1. Ma **date d'obligation d'émettre** en électronique (catégorie micro/TPE) est‑elle
   bien septembre 2027 à ce jour ?
2. En **franchise 293 B**, quelle est l'**étendue exacte** de mes obligations
   d'e‑invoicing **et** d'e‑reporting (notamment e‑reporting de paiement) ?
3. Suis‑je toujours **dans les seuils** de la franchise, compte tenu des évolutions
   récentes ? Quel impact si je les franchis ?
4. Quelle **formulation** exacte des mentions (293 B) et des **4 nouvelles mentions**
   dois‑je porter, pour une **prestation de services** B2B ?
5. Quel **codage TVA** (EN 16931 / Factur‑X) pour la franchise : catégorie et motif ?
6. La **loi anti‑fraude « logiciel de caisse »** me concerne‑t‑elle si je n'encaisse
   que du **B2B par virement** ? Et si j'ouvre le SaaS au **B2C** ?
7. Recommandes‑tu une **PDP** en particulier pour un profil TPE, et à quel coût ?
8. Quelles **obligations d'archivage / valeur probante** pour mes factures émises ?

---

## 8. Rappel

Cette revue **n'engage pas** et **ne certifie rien**. Elle sert à **cadrer** le
travail réglementaire et à **préparer** la validation par un professionnel
habilité. Aucune ligne de la `COMPLIANCE_MATRIX` ne doit passer à « CONFORME »
sans **preuve officielle datée** et, pour les points fiscaux, **avis d'un
expert‑comptable**.
