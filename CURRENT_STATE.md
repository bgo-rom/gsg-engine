# CURRENT_STATE.md — État Courant du Projet (« Terraform State »)
> **Statut : LOI + DONNÉE VIVANTE.** Ce fichier est la photographie de l'avancement **réel** du dépôt.
> **Règle absolue** : l'agent qui termine une tâche met à jour ce fichier **AVANT** sa réponse finale (AI_SOP §8).
> Une livraison sans mise à jour de `CURRENT_STATE.md` est **INVALIDE** — au même titre qu'un test rouge.
> Tout agent entrant le lit **en premier** (template T0 de `docs/PROMPT_TEMPLATES.md`). La mémoire d'une session précédente ne fait pas foi ; **ce fichier fait foi**.

---

## 1. TABLEAU DE BORD

| Indicateur | Valeur |
|---|---|
| **Jalon en cours** | M0 — Fenêtre + carte cliquable (**NON DÉMARRÉ**) |
| **Dernière mise à jour** | 2026-07-07 — Claude (session bootstrap du framework) |
| **Build `dotnet build`** | ⚫ N/A — aucune solution .NET créée |
| **Tests `dotnet test`** | ⚫ N/A — aucun test |
| **Déterminisme (StateHash headless)** | ⚫ N/A |
| **Git** | 🔴 Dépôt NON initialisé — aucun commit |

Légende : 🟢 vert (preuve exécutée) · 🔴 rouge / manquant (préciser quoi) · ⚫ N/A (pas encore applicable)

## 2. DERNIÈRE MODIFICATION EFFECTUÉE

- **Commit** : aucun (git non initialisé).
- **Contenu** : création complète du Framework de Contexte IA — `CLAUDE.md`, `AGENTS.md`, `CURRENT_STATE.md`, `.editorconfig`, `Directory.Build.props`, `docs/` (TDD, `AI_SOP.md`, `GAME_DICTIONARY.md`, `PROMPT_TEMPLATES.md`, gabarits spec/ADR).

## 3. TÂCHE IMMÉDIATE SUIVANTE

1. `git init` + premier commit du framework — message proposé : `chore: bootstrap AI context framework`.
2. Rédiger `docs/specs/001_m0_carte_cliquable.md` (à partir de `docs/specs/_TEMPLATE_spec.md`), la faire valider.
3. Dérouler `docs/AI_SOP.md` sur cette spec : solution .NET 8, projets `src/App` + `src/Map` + `tests/`, chargement ColorMap, LookupMap, pan/zoom, Picking.

## 4. EN COURS / BLOQUÉ

- **En cours** : rien.
- **Bloqué** : rien.
- **Dérogations actives** : aucune.

## 5. JOURNAL DES SESSIONS (append-only — conserver les 10 dernières lignes)

| Date | Agent | Fait | Résultat |
|---|---|---|---|
| 2026-07-07 | Claude | Bootstrap du Framework de Contexte IA (lois, SOP, dictionnaire, templates, state, lint) | Pas de build — aucun code encore |

---

## PROTOCOLE DE MISE À JOUR (pour l'agent sortant — obligatoire)

1. **Remplacer** (pas d'append) les sections 1 à 4 par l'état **constaté** : coller le verdict effectif de `dotnet build` / `dotnet test`, jamais l'espéré.
2. **Ajouter UNE ligne** au journal (§5) ; supprimer la plus ancienne au-delà de 10 lignes.
3. Dates en **ISO (AAAA-MM-JJ)**. Jamais « hier », « récemment », « la dernière fois ».
4. **Rouge = rouge.** Un test qui échoue s'écrit 🔴 avec le nom exact du test. Interdiction absolue de « verdir » le tableau pour clore proprement une session.
5. La « tâche immédiate suivante » (§3) doit être exécutable par un agent **sans aucun souvenir** de cette session : nommer les fichiers exacts, les specs, les commandes.
6. Si la session a été interrompue en plein travail : le déclarer en §4 avec l'état exact (fichiers à moitié écrits, tests rouges) — c'est le seul endroit où un état sale est acceptable, à condition d'être documenté.
