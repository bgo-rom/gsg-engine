# SPEC NNN — {{Titre de la feature}}
> Statut : DRAFT | VALIDÉE | LIVRÉE — {{date}}
> Classe SOP : A | B | C | D

## Objectif
{{1 à 3 phrases : le problème résolu, du point de vue du joueur ou du moteur.}}

## Périmètre
- **Inclus** : {{liste}}
- **Exclus** (explicitement hors-scope) : {{liste — c'est la ligne anti-scope-creep}}

## Comportement attendu
- Entrées : {{Commands, données /data, champs GameState lus}}
- Sorties : {{champs GameState écrits, affichage}}
- Règles : {{formules, barèmes, bornes, cas limites}}

## Critères d'acceptation (testables)
- [ ] {{ex. Un tick Daily avec 2 pays et taxe 0.3 produit X ± 0.01}}
- [ ] {{ex. Le tick vide ne modifie que GameDate}}
- [ ] Déterminisme : 2 runs même seed → StateHash identique
- [ ] `dotnet build` + `dotnet test` verts

## Notes / risques
{{dépendances sur d'autres specs, questions ouvertes, impact perfs attendu}}
