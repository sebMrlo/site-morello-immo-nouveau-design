# COMPLIANCE_MATRIX — matrice de conformité

> Garde‑fou documentaire (cahier des charges §44). **Aucune fonctionnalité
> réglementaire n'est considérée conforme sans preuve documentaire.** Ce fichier
> est un **squelette** : il ne préjuge d'aucune conformité et doit être renseigné
> à partir des **sources officielles** (DGFiP / impots.gouv.fr, AFNOR pour les
> normes XP) et validé avec un **expert‑comptable**.

## Légende `STATUT`

`À VÉRIFIER` · `SOURCE CONFIRMÉE` · `IMPLÉMENTÉ` · `TESTÉ` · `CONFORME (preuve jointe)`

## Matrice

| Exigence | Source officielle | Version | Implémentation | Test | Statut | Date de vérification |
|---|---|---|---|---|---|---|
| Distinction solution de facturation / plateforme agréée (PDP) | *(à renseigner)* | | conception (adaptateurs) | — | À VÉRIFIER | |
| Formats du socle (Factur‑X / UBL / CII) acceptés | *(à renseigner)* | | — | — | À VÉRIFIER | |
| Profils / formats applicables | XP Z12‑012 *(à confirmer)* | | — | — | À VÉRIFIER | |
| API d'interfaçage avec plateforme agréée | XP Z12‑013 *(à confirmer)* | | port `ProviderAdapter` | — | À VÉRIFIER | |
| Cas d'usage B2B | XP Z12‑014 *(à confirmer)* | | — | — | À VÉRIFIER | |
| Statuts du cycle de vie de la facture | *(à renseigner)* | | machine à états | — | À VÉRIFIER | |
| Mentions obligatoires sur facture | *(à renseigner)* | | `InvoiceComplianceEngine` | — | À VÉRIFIER | |
| Données structurées minimales (socle) | *(à renseigner)* | | `CanonicalInvoice` | — | À VÉRIFIER | |
| e‑reporting (données de transaction/paiement) | *(à renseigner)* | | via PDP | — | À VÉRIFIER | |
| Calendrier d'entrée en vigueur (par taille d'entreprise) | *(à renseigner)* | | — | — | À VÉRIFIER | |
| Immatriculation de la PDP partenaire | annuaire officiel DGFiP *(à confirmer)* | | `ProviderConnection` | — | À VÉRIFIER | |
| Archivage / valeur probante / durée de conservation | *(à renseigner)* | | audit + stockage | — | À VÉRIFIER | |
| Emploi de la signalétique « solution compatible » | *(à renseigner)* | | — | — | À VÉRIFIER | |

*Ajouter une ligne par exigence identifiée. Joindre la preuve (lien officiel +
capture datée) au passage en `CONFORME`.*
