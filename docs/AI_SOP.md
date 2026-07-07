# AI_SOP.md — Procédure Opérationnelle Standard des Agents IA
> **Statut : LOI.** Toute tâche exécutée sur ce dépôt suit cette procédure, dans l'ordre, sans sauter d'étape.
> Analogie assumée : c'est un runbook d'exploitation. On ne « bricole pas en prod », on déroule.

---

## 0. Classification de la tâche (30 secondes, obligatoire)

Avant tout, classe la tâche reçue. La classe détermine les étapes applicables :

| Classe | Exemples | Étapes obligatoires |
|---|---|---|
| **A — Code moteur** | nouveau système, panneau UI, feature carte | 1 → 8 (toutes) |
| **B — Contenu /data** | pays, lois, événements, localisation | 1, 2, 5, 6 (validation loader), 8 |
| **C — Bugfix** | crash, désync, valeur fausse | 1, 4 (test de repro **d'abord**), 5, 6, 7, 8 |
| **D — Refactor / dette** | renommage, extraction, perf | 1 → 8 + ADR si structurel |
| **E — Question / audit** | « pourquoi X ? », revue | 1 puis réponse. **Aucune modification de fichier.** |

> [!WARNING]
> Si la tâche mélange plusieurs classes (« corrige le bug et ajoute le panneau »), **découpe en tâches séparées** et annonce le découpage à l'étape 2.

---

## 1. Charger le contexte RÉEL

- Lire : `CURRENT_STATE.md` (**en premier** — l'état réel du dépôt fait foi, pas ta mémoire), `CLAUDE.md`, `docs/GAME_DICTIONARY.md`, la section du TDD concernée, la spec `docs/specs/NNN_*.md` si elle existe.
- Lire **le contenu actuel** de chaque fichier source que la tâche va toucher ou appeler. Interdiction de raisonner de mémoire sur un fichier du projet.
- Vérifier qu'aucun ADR n'a déjà tranché le sujet (`docs/adr/`).
- **Pas de spec pour une tâche de classe A ou D ?** → Rédiger une spec courte (template : `docs/specs/_TEMPLATE_spec.md`) et la soumettre à validation à l'étape 3 en même temps que le plan.

## 2. Produire le PLAN (aucun code à cette étape)

Format imposé, court :

```markdown
## PLAN — {{titre de la tâche}}
- **Objectif** : 1 phrase.
- **Fichiers créés** : liste exacte.
- **Fichiers modifiés** : liste exacte + nature du changement (1 ligne chacun).
- **Signatures clés** : les 2–5 méthodes/structs publiques principales (signature seule).
- **Données** : champs GameState/GameDefs lus, champs GameState écrits, Commands ajoutées.
- **Tests prévus** : liste des cas (nominal, bords, invariants).
- **Risques / points ouverts** : ce qui mérite l'œil humain.
```

- Le plan respecte les 10 Commandements **par construction** (ex. : un panneau UI déclare les Commands qu'il émet, jamais une écriture d'état).
- Question bloquante ? La poser **ici**, avec ta recommandation.

## 3. 🛑 GATE HUMAINE — attendre le GO

- Soumettre le plan et **attendre la validation explicite** de l'humain.
- Pas de GO = pas de code. Un « GO sauf point 3 » = appliquer la correction puis exécuter, sans re-valider.
- Exceptions dispensées de gate : classe E (aucune écriture) ; classe B ≤ 2 fichiers de données ; correction triviale explicitement demandée (« corrige cette typo »).

## 4. Écrire les TESTS d'abord

- Créer les tests xUnit du plan dans `/tests` (miroir de l'arborescence). Ils doivent **compiler et échouer** (rouge) avant l'implémentation.
- Classe C (bugfix) : le test de reproduction du bug est **la première chose écrite**. Il échoue → le bug est capturé. Il passera → le bug est mort et ne reviendra pas.
- Invariants systématiques pour un système de simulation :
  - conservation (rien ne se crée/perd sans cause : monnaie, manpower, stocks) ;
  - tick vide (0 Command) ne change que la date ;
  - déterminisme : 2 runs même seed → états identiques (comparer un hash de GameState).

## 5. Implémenter par PETITS LOTS

- **1 à 3 fichiers par lot**, jamais « tout le système d'un coup ». Ordre : structs/données → logique → branchement (enregistrement dans le pipeline de tick, ou dans le registre des panneaux).
- Code **complet** à chaque lot (Commandement : pas de stub, pas de TODO).
- Ne toucher **que** les fichiers du plan. Découverte imprévue qui invalide le plan → retour à l'étape 2 avec un plan amendé, pas d'improvisation.

## 6. Boucle de vérification mécanique

```
dotnet build  → erreur ? corriger (l'erreur verbatim est ta spec), max 3 tentatives
dotnet test   → rouge ? idem
[classe B]    → lancer le jeu ou le loader : la validation /data doit passer
[si pertinent]→ dotnet run --project src/App -- --headless --ticks 1000
```

> [!IMPORTANT]
> **Règle des 3 tentatives** : 3 échecs sur la même erreur → STOP. Rapporter : l'erreur exacte, les 3 tentatives, ton diagnostic, 2 options. L'humain arbitre. On ne creuse pas un trou.

## 7. Auto-audit des invariants (checklist finale)

À dérouler explicitement avant livraison — répondre par oui/non, pas « probablement » :

| # | Contrôle | Comment vérifier |
|---|---|---|
| 1 | Aucun `using Raylib`/`ImGui` dans Core/Systems/Data | grep sur les fichiers touchés |
| 2 | Aucune écriture GameState hors Tick/Systems | relire les fichiers UI/Map touchés |
| 3 | Aucun `DateTime.Now` / `Guid` / `Random` non-seedé / itération de Dictionary en simulation | grep |
| 4 | Aucune allocation ni LINQ dans le hot path du tick | relire les boucles ajoutées |
| 5 | Aucune valeur de gameplay en dur dans le C# | relire les constantes ajoutées |
| 6 | Aucun TODO / NotImplementedException / code mort livré | grep |
| 7 | Vocabulaire conforme au GAME_DICTIONARY | relire noms publics ajoutés |
| 8 | Tests nouveaux présents ET verts | sortie `dotnet test` |

## 8. Livraison

> [!IMPORTANT]
> **Avant** de rédiger la réponse finale : mettre à jour `CURRENT_STATE.md` (sections 1–4 remplacées par l'état constaté, une ligne ajoutée au journal — protocole en bas de ce fichier). **Une livraison sans mise à jour de `CURRENT_STATE.md` est invalide**, au même titre qu'un test rouge. C'est le passage de relais : le prochain agent — peut-être un autre modèle — ne connaîtra du projet que ce que ce fichier dit.

Format de fin de tâche, systématique :

```markdown
## LIVRAISON — {{titre}}
- **Fait** : 2–4 puces (quoi, où).
- **Fichiers** : créés / modifiés.
- **Tests** : X passés / Y total (coller la dernière ligne de `dotnet test`).
- **Checklist §7** : OK (ou dérogations explicites).
- **CURRENT_STATE.md** : mis à jour ✅ (obligatoire).
- **Commit proposé** : `feat(economy): ... (spec 012)`
- **Signalements hors-scope** : améliorations repérées, NON appliquées (Commandement 10).
```

- Décision structurelle prise en cours de route → créer/mettre à jour un ADR (`docs/adr/_TEMPLATE_adr.md`) dans la même livraison.

---

## Protocoles d'exception

| Situation | Conduite à tenir |
|---|---|
| Spec ambiguë ou contradictoire avec le TDD | STOP à l'étape 2. Une question, une recommandation. |
| Le plan validé s'avère infaisable en cours d'implémentation | STOP. Plan amendé → nouvelle gate (étape 3). |
| Besoin d'une dépendance NuGet | STOP. Proposer un ADR (alternatives, coût, risque). Jamais d'ajout direct. |
| Test existant cassé par la tâche | Ne **jamais** modifier le test pour le faire passer sans accord humain. Le test est présumé avoir raison. |
| Instruction humaine qui viole un Commandement | Le signaler en 1 phrase, demander confirmation. Si confirmé : exécuter + mettre à jour CLAUDE.md/ADR dans le même commit. |
| Fichier attendu introuvable / arborescence différente du TDD | Ne pas « deviner ». Lister ce qui existe, signaler l'écart. |
