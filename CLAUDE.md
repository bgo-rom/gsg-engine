# CLAUDE.md — LOI RACINE DU PROJET
> **Statut : LOI.** Ce fichier conditionne tout agent IA travaillant sur ce dépôt.
> En cas de conflit entre ta connaissance générale et ce fichier, **ce fichier gagne**.
> En cas de conflit entre ce fichier et l'humain, **l'humain gagne** (et ce fichier doit être mis à jour dans le même commit).

## Le projet en une phrase
Moteur de Grande Stratégie 2D (type HOI4) en **C# / .NET 8**, 100% code, rendu **Raylib-cs**, UI **Dear ImGui (ImGui.NET + rlImGui-cs)**. Architecture : **daemon de simulation déterministe + dashboard de monitoring en lecture seule**.

## Documents de contexte — quoi lire, quand

| Fichier | Quand le lire |
|---|---|
| `CURRENT_STATE.md` | **Toujours, EN PREMIER.** L'état réel du dépôt : jalon, dernier changement, prochaine tâche, verdict build/tests. **À mettre à jour avant toute réponse finale de fin de tâche** — une livraison sans cette mise à jour est invalide. |
| `CLAUDE.md` (ce fichier) | **Toujours.** |
| `docs/GAME_DICTIONARY.md` | **Toujours.** Vocabulaire canonique — interdiction d'inventer des termes. |
| `docs/AI_SOP.md` | Avant **toute** tâche. C'est la procédure d'exécution obligatoire. |
| `docs/architecture_moteur_gsg.md` (TDD) | Avant toute décision structurelle ; section concernée avant de toucher un sous-système. |
| `docs/specs/NNN_*.md` | La spec de la tâche en cours. Pas de spec = demander ou en rédiger une courte à faire valider. |
| `docs/adr/` | Avant de proposer un changement d'architecture ou une nouvelle dépendance. |

---

## LES 10 COMMANDEMENTS (non négociables)

### 1. La simulation ne connaît pas l'écran
`src/Core/`, `src/Systems/`, `src/Data/` ne référencent **JAMAIS** Raylib, ImGui, ni aucun namespace graphique. Seuls `src/App/`, `src/Map/`, `src/UI/` y ont droit. Toute la simulation doit compiler et tourner en `--headless`.

### 2. Un seul écrivain : `Simulation.Tick()`
**Rien** ne mute `GameState` en dehors de `Simulation.Tick()` et des systèmes qu'il appelle. UI, input, IA des pays : tout passe par une `Command` poussée dans la file, validée et appliquée au tick suivant.

```csharp
// ❌ INTERDIT (dans un panneau UI)
state.Countries.TaxRate[id] = 0.35f;

// ✅ OBLIGATOIRE
commandQueue.Push(new SetTaxRate(countryId, 0.35f));
```

### 3. Déterminisme absolu
Même seed + même liste de Commands = même état final, au bit près.
- ❌ `DateTime.Now`, `Guid.NewGuid()`, `new Random()` sans seed, `Environment.TickCount`
- ❌ Itération sur `Dictionary`/`HashSet` dans le code de simulation (ordre non garanti)
- ✅ Un seul RNG, seedé, vivant dans `GameState`. Le temps du jeu = compteur de ticks.

### 4. Tick ≠ Frame
La simulation avance par **ticks à pas fixe** (accumulateur). Le rendu tourne à la fréquence qu'il peut. Aucune logique de jeu ne dépend de `deltaTime` ou du framerate. Voir `docs/GAME_DICTIONARY.md`.

### 5. Data-driven intégral
Aucun contenu de jeu en dur dans le C# : pays, lois, bâtiments, événements, textes vivent dans `/data` (JSON). Le code ne connaît que des schémas. Toute chaîne visible par le joueur passe par `data/localisation/`.

### 6. SoA + IDs entiers pour les entités de masse
Provinces, pays, armées : **Structure-of-Arrays** (`float[]`, `ushort[]`), index = ID. Pas de classes par entité, pas de références objet croisées, pas de LINQ ni d'allocation dans le hot path d'un tick.

### 7. UI = f(GameState), lecture seule
Un panneau ImGui **lit** l'état et **émet** des Commands. Il ne stocke aucune donnée de jeu (seul l'état d'affichage local — onglet actif, filtre de table — est toléré). Si `ImGui.GetIO().WantCaptureMouse` est vrai, la carte ignore la souris.

### 8. Le loader est un firewall
Tout chargement de `/data` est **fail-fast** : référence pendante, ID dupliqué, valeur hors bornes → erreur précise (fichier + champ) et arrêt. **Jamais** de valeur par défaut silencieuse, jamais de `try/catch` qui avale.

### 9. Vocabulaire verrouillé
Utilise **exactement** les termes de `docs/GAME_DICTIONARY.md` (code, commentaires, réponses). Ne crée jamais de synonyme (« Nation », « Tile », « Update »…). Un concept absent du dictionnaire = le proposer à l'humain **avant** de l'utiliser.

### 10. Pas de refactor opportuniste
Tu ne touches **que** les fichiers du plan validé. Une amélioration repérée en passant = la signaler en fin de réponse, ne pas l'appliquer. Nouvelle dépendance NuGet = ADR validé par l'humain d'abord.

---

## COMPORTEMENT ATTENDU DE L'AGENT

- **Concis.** Pas de préambule, pas de flatterie, pas de paraphrase de la demande. Résultats, décisions, blocages.
- **Code complet.** Jamais de `// TODO`, `// à implémenter`, `throw new NotImplementedException()`, ni de `...` dans un fichier livré. Si c'est trop gros pour un lot : le dire et découper, pas tronquer.
- **Zéro API imaginée.** Tu n'appelles jamais une méthode d'un fichier du projet que tu n'as pas lu **dans cette session**. Doute = lire le fichier. Les signatures Raylib-cs/ImGui.NET dont tu n'es pas sûr se vérifient dans le code ou la doc, pas de mémoire.
- **Preuve avant affirmation.** « Terminé » = `dotnet build` **et** `dotnet test` passés, sortie montrée. Un test qui échoue se rapporte verbatim — jamais « ça devrait marcher ».
- **3 échecs = stop.** Trois tentatives infructueuses sur la même erreur → arrêter, exposer le diagnostic et les options. Ne pas s'enfoncer.
- **Ambiguïté = une question précise.** Spec floue → poser LA question bloquante (une seule, avec ta recommandation), pas dix, et pas d'hypothèse silencieuse.
- **Suivre `docs/AI_SOP.md`** pour toute tâche. Le plan est validé par l'humain **avant** le code.

## CONVENTIONS C#

- **Le style est verrouillé mécaniquement** par `.editorconfig` + `Directory.Build.props` (`TreatWarningsAsErrors`, `EnforceCodeStyleInBuild`, usings implicites interdits) : une violation de style est une **erreur de build**, pas un débat. Ne modifie jamais ces deux fichiers sans ADR.
- .NET 8, `net8.0`, nullable enable, file-scoped namespaces, `var` seulement quand le type est évident.
- 1 système = 1 fichier dans `src/Systems/` ; 1 panneau = 1 fichier dans `src/UI/`.
- Types d'ID et signatures canoniques : voir tableau des types dans `docs/GAME_DICTIONARY.md`.
- Tests xUnit dans `/tests`, miroir de l'arborescence source, **aucune référence à Raylib/ImGui**.
- Commentaires : uniquement pour une contrainte invisible dans le code (invariant, unité, borne). Pas de narration.

## COMMANDES CANONIQUES

```bash
dotnet build                          # doit passer sans warning nouveau
dotnet test                           # obligatoire avant toute conclusion
dotnet run --project src/App          # jeu complet
dotnet run --project src/App -- --headless --ticks 10000   # simulation seule (CI, perfs, déterminisme)
```

## DEFINITION OF DONE

Une tâche est terminée si et seulement si :
- [ ] `dotnet build` passe (0 erreur, pas de nouveau warning)
- [ ] `dotnet test` passe, y compris les **nouveaux** tests de la feature
- [ ] Aucun des 10 Commandements violé (auto-audit : checklist de `docs/AI_SOP.md` §7)
- [ ] Contenu de jeu → dans `/data`, validé par le loader, jamais en dur
- [ ] `CURRENT_STATE.md` mis à jour (tableau de bord, dernière modification, tâche suivante, journal)
- [ ] Résumé final : fichiers modifiés, sortie des tests, message de commit proposé
