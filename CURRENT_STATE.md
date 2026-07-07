# CURRENT_STATE.md — État Courant du Projet (« Terraform State »)
> **Statut : LOI + DONNÉE VIVANTE.** Ce fichier est la photographie de l'avancement **réel** du dépôt.
> **Règle absolue** : l'agent qui termine une tâche met à jour ce fichier **AVANT** sa réponse finale (AI_SOP §8).
> Une livraison sans mise à jour de `CURRENT_STATE.md` est **INVALIDE** — au même titre qu'un test rouge.
> Tout agent entrant le lit **en premier** (template T0 de `docs/PROMPT_TEMPLATES.md`). La mémoire d'une session précédente ne fait pas foi ; **ce fichier fait foi**.

---

## 1. TABLEAU DE BORD

| Indicateur | Valeur |
|---|---|
| **Jalon en cours** | M0 — Fenêtre + carte cliquable (**EN COURS** : socle graphique livré + ColorMap de test générée) |
| **Dernière mise à jour** | 2026-07-07 — Claude (outil ColorMap de test) |
| **Build `dotnet build`** | 🟢 « La génération a réussi. 0 Avertissement(s) 0 Erreur(s) » |
| **Tests `dotnet test`** | ⚫ N/A — aucun projet de test (dérogation actée : spec 001 = 100 % code graphique ; `/tests` naît en M1) |
| **Déterminisme (StateHash headless)** | ⚫ N/A |
| **Git** | 🟢 Initialisé, 1 commit (`26fa20f` framework). ⚠️ Spec 001 NON commitée. |

Légende : 🟢 vert (preuve exécutée) · 🔴 rouge / manquant (préciser quoi) · ⚫ N/A (pas encore applicable)

## 2. DERNIÈRE MODIFICATION EFFECTUÉE

- **Commit** : aucun pour ces livraisons (en attente) — proposé : `feat(app): bootstrap Raylib+ImGui window (spec 001)` puis `feat(tools): test colormap generator + data/map/provinces.png`.
- **Contenu** : (a) spec 001 livrée — `gsg_engine.sln`, `src/App/App.csproj` (net8.0 ; Raylib-cs 8.0.0, ImGui.NET 1.91.6.1, rlImgui-cs 3.2.0 ; restore local via `nuget.config` → `.packages/`), `src/App/Program.cs`, `.gitignore` ; smoke test 5 s OK. (b) `tools/generate_test_colormap.py` (Python stdlib, zéro dépendance) → `data/map/provinces.png` 512×512, 4 Provinces : `#FF0000` bande ouest, `#00FF00` bande centrale, `#0000FF` bande est, `#FFFF00` île circulaire (centre 256,256 ; r=80). Vérifié par relecture du fichier : exactement 4 couleurs uniques, zéro anti-aliasing.

## 3. TÂCHE IMMÉDIATE SUIVANTE

1. Committer les livraisons en attente (messages ci-dessus).
2. Rédiger `docs/specs/002_m0_colormap_picking.md` : projet `src/Map` + `provinces.png` de test, chargement ColorMap → LookupMap, `Camera2D` pan/zoom, Picking (affichage de l'ID de la province cliquée). Créer le projet `tests/` (la logique LookupMap/adjacence est testable sans Raylib via des buffers de pixels).
3. Dérouler `docs/AI_SOP.md` sur la spec 002 (plan → gate → tests → code).

## 4. EN COURS / BLOQUÉ

- **En cours** : rien (livraison 001 close).
- **Bloqué** : rien.
- **Dérogations actives** : spec 001 sans tests xUnit (code graphique uniquement — voir spec).

## 5. JOURNAL DES SESSIONS (append-only — conserver les 10 dernières lignes)

| Date | Agent | Fait | Résultat |
|---|---|---|---|
| 2026-07-07 | Claude | Bootstrap du Framework de Contexte IA (lois, SOP, dictionnaire, templates, state, lint) | Pas de build — aucun code encore |
| 2026-07-07 | Claude | Spec 001 : sln + src/App (Raylib 8.0.0/ImGui), Program.cs, .gitignore | 🟢 build 0 warn ; smoke test 5 s OK |
| 2026-07-07 | Claude | Outil tools/generate_test_colormap.py → data/map/provinces.png (4 Provinces) | 🟢 PNG relu : 4 couleurs, 0 anti-aliasing |

---

## PROTOCOLE DE MISE À JOUR (pour l'agent sortant — obligatoire)

1. **Remplacer** (pas d'append) les sections 1 à 4 par l'état **constaté** : coller le verdict effectif de `dotnet build` / `dotnet test`, jamais l'espéré.
2. **Ajouter UNE ligne** au journal (§5) ; supprimer la plus ancienne au-delà de 10 lignes.
3. Dates en **ISO (AAAA-MM-JJ)**. Jamais « hier », « récemment », « la dernière fois ».
4. **Rouge = rouge.** Un test qui échoue s'écrit 🔴 avec le nom exact du test. Interdiction absolue de « verdir » le tableau pour clore proprement une session.
5. La « tâche immédiate suivante » (§3) doit être exécutable par un agent **sans aucun souvenir** de cette session : nommer les fichiers exacts, les specs, les commandes.
6. Si la session a été interrompue en plein travail : le déclarer en §4 avec l'état exact (fichiers à moitié écrits, tests rouges) — c'est le seul endroit où un état sale est acceptable, à condition d'être documenté.
