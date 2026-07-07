# PROMPT_TEMPLATES.md — Boîte à outils de prompts (usage humain)
> **Public : l'humain.** Copier le template, remplir les `{{trous}}`, supprimer les lignes marquées *(optionnel)* non utilisées, coller à l'agent.
> Chaque template force l'agent dans `AI_SOP.md` : plan d'abord, gate humaine, tests, vérification mécanique.
> Règle d'or : **une tâche = un prompt = une session**. Ne pas enchaîner deux features dans la même conversation.
> **Toute nouvelle session — et à plus forte raison tout changement de modèle ou d'outil (Claude → Codex/Cursor…) — commence par T0.**

---

## T0 — Prise de Service (changement d'IA / boot de session) 🔐

**Quand** : première interaction avec un agent, quel qu'il soit. C'est le **handshake de sécurité** : il vérifie que l'agent a chargé les lois et l'état réel du projet **avant** de lui confier quoi que ce soit.

```text
[TÂCHE] Prise de service (classe E — AUCUNE modification de fichier, AUCUN code).

Tu es un nouvel agent sur ce dépôt. Procédure impérative :

1. LIS intégralement, dans cet ordre : CURRENT_STATE.md, CLAUDE.md,
   docs/AI_SOP.md, docs/GAME_DICTIONARY.md.

2. RÉPONDS exactement dans ce format, rien de plus :
   ## PRISE DE SERVICE
   - **Contraintes** : les 3 contraintes techniques les plus structurantes
     du projet (3 puces, 1 ligne chacune, avec le numéro du Commandement).
   - **État** : jalon en cours, verdict build/tests, et la tâche immédiate
     suivante — tels que lus dans CURRENT_STATE.md, sans interprétation.
   - **Serment** : recopie : « Je ne produis aucun code sans plan validé
     (AI_SOP §3) et je mets à jour CURRENT_STATE.md avant ma réponse finale. »

3. Puis STOP. Aucun code, aucune suggestion, aucune initiative, aucune
   question sauf si un des 4 fichiers est introuvable ou contradictoire
   (auquel cas : le signaler, c'est tout). Tu attends mon GO et la tâche.
```

**Contrôle humain du handshake** — rejeter et relancer T0 si la réponse :
- contient du code ou une proposition d'amélioration ;
- dépasse ~15 lignes ;
- décrit un état du projet différent de `CURRENT_STATE.md` (l'agent a « imaginé » l'état) ;
- omet le serment.

---

## T1 — Nouveau System de simulation

**Quand** : ajouter une logique qui tourne dans le pipeline de `Tick()` (économie, attrition, ravitaillement…).

```text
[TÂCHE] Créer un nouveau System : {{NomSystem}}System (classe A — suivre docs/AI_SOP.md).

[SPEC]
- Rôle : {{ce que le système calcule, en 2–4 lignes}}
- Cadence : {{Hourly | Daily | Weekly}}
- Position dans le pipeline de Tick : {{après XxxSystem / avant YyySystem}}
- Lit : {{champs GameState + GameDefs concernés}}
- Écrit : {{champs GameState concernés}}
- Nouvelles Commands : {{liste ou "aucune"}}
- Invariant(s) à garantir : {{ex. conservation de la monnaie mondiale ; borne 0..1 sur stability}}

[RÈGLES DE CALCUL]
{{formules / barèmes / cas limites, même approximatifs — l'agent proposera le reste dans le plan}}

[CONTRAINTES]
- SoA, zéro allocation dans la boucle, IDs entiers (Commandements 3 et 6).
- Étape PLAN d'abord (SOP §2) : n'écris AUCUN code avant mon GO.
- Tests obligatoires : tick vide, invariant(s) ci-dessus, déterminisme (StateHash).
```

---

## T2 — Nouveau Panel ImGui

**Quand** : ajouter un panneau du dashboard (vue économie, liste d'armées, écran diplomatie…).

```text
[TÂCHE] Créer un nouveau Panel : {{NomPanel}}Panel (classe A — suivre docs/AI_SOP.md).

[SPEC]
- Ouverture : {{raccourci / bouton topbar / clic sur une Province ou un Country}}
- Affiche : {{données, colonnes de table, tri/filtres attendus}}
- Actions utilisateur : {{boutons/inputs}} → Commands émises : {{SetTaxRate(...), ...}}
- Source des données : lecture seule de GameState.{{...}} et GameDefs.{{...}}

[MAQUETTE TEXTE] (optionnel)
{{croquis ASCII ou liste ordonnée des sections du panneau}}

[CONTRAINTES]
- Commandements 1, 2, 7 : lecture seule sur GameState, toute action = Command, aucun accès Raylib.
- État local toléré : tri/filtre/onglet uniquement.
- Textes via data/localisation/ (clés {{prefix}}_*), rien en dur.
- PLAN d'abord, GO requis. Utiliser ImGui.BeginTable pour toute liste > 5 lignes.
```

---

## T3 — Nouveau type de données JSON (Def)

**Quand** : introduire un nouveau type de contenu (ressource, doctrine, traité…) chargé depuis `/data`.

```text
[TÂCHE] Créer un nouveau type de Def : {{NomDef}} (classe A — suivre docs/AI_SOP.md).

[SPEC]
- Répertoire : data/common/{{dossier}}/
- Champs : {{nom : type : bornes/contraintes, un par ligne}}
- Références vers d'autres Defs : {{ex. "resource": StringKey vers resources.json}}
- Utilisé par : {{System(s) ou Panel(s) consommateurs}}

[LIVRABLES ATTENDUS]
1. Struct {{NomDef}} dans GameDefs (immutable) + interning des StringKeys.
2. Loader fail-fast dans src/Data/ : ID dupliqué, référence pendante, borne violée
   → erreur "fichier + champ + raison" (Commandement 8). Aucun défaut silencieux.
3. JSON Schema dans data/schemas/{{nom}}.schema.json.
4. Fichier d'exemple data/common/{{dossier}}/{{exemple}}.json (3 entrées réalistes).
5. Tests : chargement nominal + 3 tests de rejet (1 par type d'erreur).

[CONTRAINTES] PLAN d'abord, GO requis. HotReload doit continuer de fonctionner.
```

---

## T4 — Génération de contenu en masse (/data uniquement)

**Quand** : produire ou modifier du contenu de jeu (pays, ScriptedEvents, localisation) sans toucher au C#. Classe B : pas de gate si ≤ 2 fichiers.

```text
[TÂCHE] Générer du contenu /data (classe B — AUCUN fichier C# ne doit être modifié).

[CIBLE] {{ex. 8 ScriptedEvents politiques pour FRA, période 1936–1939}}
[FICHIER(S)] {{data/events/fra_politics.json, data/localisation/fr.json}}
[SCHÉMA] Respecter data/schemas/{{schema}}.json — vocabulaire Trigger/Effect FERMÉ :
n'utilise QUE les opérateurs existants ; s'il en manque un, STOP et propose-le, ne l'invente pas.

[DIRECTION ÉDITORIALE]
- Ton : {{sobre / dramatique / historique}}
- Équilibrage : {{bornes des effets, ex. add_stat stability entre -0.15 et +0.15}}
- Contexte : {{éléments historiques ou de gameplay à respecter}}

[VALIDATION] Après écriture : lancer le Loader (boot headless) et coller la sortie.
Toute clé de texte ajoutée doit exister dans data/localisation/.
```

---

## T5 — Bugfix avec reproduction

**Quand** : comportement erroné, crash, ou désynchronisation de déterminisme.

```text
[TÂCHE] Bugfix (classe C — suivre docs/AI_SOP.md : test de repro AVANT tout fix).

[SYMPTÔME] {{ce qui se passe, verbatim : message d'erreur, valeur observée}}
[ATTENDU] {{ce qui devrait se passer}}
[REPRO] {{étapes exactes, ou : seed {{S}}, scénario {{X}}, --headless --ticks {{N}}}}
[PISTE] (optionnel) {{soupçon humain — l'agent doit le vérifier, pas le croire}}

[PROCÉDURE IMPOSÉE]
1. Écrire d'abord le test xUnit qui reproduit le bug (il doit ÉCHOUER). Me montrer la sortie.
2. Diagnostiquer la cause racine — pas de fix-symptôme, pas de try/catch pansement.
3. Fixer, prouver : test de repro vert + suite complète verte (sortie de dotnet test).
4. Règle des 3 tentatives (SOP §6) : bloqué = STOP + diagnostic + options.
[INTERDIT] Modifier un test existant pour le faire passer. Refactorer au passage.
```

---

## T6 — Audit / question d'architecture (lecture seule)

**Quand** : comprendre, vérifier, comparer — sans rien modifier.

```text
[TÂCHE] Audit lecture seule (classe E — AUCUNE modification de fichier).
[QUESTION] {{ex. le hot path d'EconomySystem alloue-t-il ? quelles violations du Commandement 2 dans src/UI/ ?}}
[PÉRIMÈTRE] {{fichiers/dossiers à inspecter}}
[FORMAT DE RÉPONSE] Constats avec références fichier:ligne, verdict par constat
(CONFIRMÉ / SUSPECT), puis recommandation en ≤ 5 lignes. Pas de code réécrit.
```

---

## Annexe — micro-tâches (dispense de template)

Pour une correction triviale et non ambiguë (typo, renommage local, ajustement d'une valeur dans /data), un prompt d'une ligne suffit **à condition** de nommer le fichier exact :
`Corrige {{quoi}} dans {{chemin/fichier}} — trivial, pas de plan, mais dotnet build + test avant livraison.`
