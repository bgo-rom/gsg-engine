# Document de Conception Technique (TDD)
## Moteur de Grande Stratégie 2D — "From Scratch", 100% Code, Assisté par IA

> **Public cible** : développeur avec profil infra/réseau (Debian, Proxmox) et trading quantitatif temps réel.
> **Principe directeur** : un jeu de grande stratégie n'est pas un "jeu vidéo" au sens classique — c'est un **serveur de simulation déterministe** avec un **dashboard de monitoring** branché dessus. Toute l'architecture découle de cette analogie.

---

## 1. CHOIX DE LA STACK TECHNIQUE

### 1.1 Langage : **C# (.NET 8+)** — recommandation finale

| Critère | C++ | **C# (.NET 8+)** | Python |
|---|---|---|---|
| Perf boucle de simulation | ★★★★★ | ★★★★☆ (JIT + structs + `Span<T>`) | ★☆☆☆☆ |
| Qualité du code généré par IA | ★★★☆☆ (UB, gestion mémoire, hallucinations subtiles) | ★★★★★ (corpus massif, erreurs attrapées à la compilation) | ★★★★★ |
| Détection des hallucinations IA | Faible (compile puis crash en runtime) | **Forte (typage strict + compilateur verbeux)** | Nulle (erreurs à l'exécution) |
| Tooling sans IDE lourd | CMake (friction élevée) | `dotnet build/run/test` en CLI, style `make` | pip/venv |
| Écosystème Raylib | natif | **Raylib-cs** (binding officiel, mature) | raylib-py (lent) |

**Justification de l'arbitrage :**
- **Python est éliminé** : simuler ~200 pays × ~15 000 provinces × économie/logistique/militaire à chaque tick est un problème CPU-bound à boucles serrées. L'interpréteur CPython est 50–100× trop lent ; NumPy vectorisé forcerait une architecture illisible pour l'IA générative.
- **C++ est éliminé** malgré ses performances : le code généré par IA en C++ produit des bugs *silencieux* (undefined behavior, dangling pointers, règles de move-semantics). Sans formation game dev/C++, ces bugs sont indétectables en review. Le coût de la dette technique dépasse le gain de performance.
- **C# gagne** : ~80–90% des performances du C++ sur ce type de charge (le hot path utilise des `struct`, des tableaux plats et zéro allocation dans la boucle), tout en offrant un **compilateur qui refuse le code halluciné**. C'est le meilleur "harnais de sécurité" possible pour un développement 100% IA.
- Analogie trading : C# est au C++ ce que votre bot en langage managé bien profilé est au HFT en FPGA — largement suffisant tant qu'on ne vise pas la microseconde. Ici, un tick de simulation a un budget de plusieurs **millisecondes**.

**Packages retenus :**
- `Raylib-cs` — binding C# officiel de Raylib (fenêtre, rendu 2D, input, textures, shaders).
- `ImGui.NET` + `rlImGui-cs` — Dear ImGui bridgé sur Raylib.
- `System.Text.Json` (source-generated) — sérialisation données de jeu / sauvegardes.
- `xUnit` — tests de la simulation (aucune dépendance graphique).

### 1.2 Librairie UI : **Dear ImGui** (via ImGui.NET) — pas RayGUI

- **Dear ImGui est conçu exactement pour votre cas** : UI massive type tableau de bord, en mode immédiat, 100% code, zéro éditeur visuel. C'est l'outil standard des outils internes de studios AAA et… des dashboards de trading propriétaires.
- **Mode immédiat** = l'UI est *redéclarée à chaque frame* comme une fonction de l'état : `UI = f(GameState)`. Pas de synchronisation widget↔état, pas de callbacks, pas de state UI caché — la classe de bugs la plus fréquente en UI disparaît.
- Fourni d'office : tables triables/filtrables (`ImGui.BeginTable`), plots (`ImPlot` si besoin), docking multi-fenêtres, arbres, tooltips — soit 90% de l'UI d'un HOI4-like sans rien coder.
- **RayGUI est rejeté** : trop rudimentaire (pas de tables complexes, pas de docking, layout manuel). Correct pour un menu, insuffisant pour 40 panneaux économiques.
- L'IA générative connaît extrêmement bien l'API ImGui (corpus énorme) → taux d'hallucination très bas sur ce composant.
- **Répartition des responsabilités** : Raylib rend la carte (monde) ; ImGui rend tout le reste (panneaux, topbar, popups). Les deux coexistent dans la même frame sans conflit via `rlImGui`.

---

## 2. ARCHITECTURE SYSTÈME (Paradigme Infra/Trading)

### 2.1 La Game Loop = un daemon + un client de monitoring

Correspondance directe avec vos domaines :

| Concept jeu | Équivalent infra/trading |
|---|---|
| Tick de simulation (ex. 1 tick = 1 heure de jeu) | Tick de marché / itération de la boucle du bot |
| Boucle de rendu (60 FPS) | Dashboard Grafana qui *lit* l'état, sans jamais l'écrire |
| `GameState` central | Base in-memory (Redis-like) / order book |
| File de commandes du joueur | File d'ordres envoyée à l'exchange |
| Vitesse de jeu 1–5 / pause | Throttling du scheduler du daemon |
| Sauvegarde | Snapshot / dump RDB |
| Rejouabilité déterministe | Backtest : mêmes inputs → mêmes outputs |

**Structure : deux boucles découplées, un seul sens d'écriture.**

```
┌─────────────────────────────────────────────────────────┐
│ BOUCLE PRINCIPALE (60 FPS, thread principal)            │
│                                                         │
│  1. Input      → traduit clics/raccourcis en Commands   │
│  2. Scheduler  → si accumulator >= tickDuration :       │
│                    Simulation.Tick(state, commands)     │
│                    (0, 1 ou N ticks par frame selon     │
│                     la vitesse de jeu — fixed timestep) │
│  3. Render     → dessine carte + UI en LISANT state     │
└─────────────────────────────────────────────────────────┘
```

- **Fixed timestep avec accumulateur** : la simulation avance par pas de temps *fixes et discrets* (comme un backtest bougie par bougie), jamais par `deltaTime` variable. C'est la condition n°1 du déterminisme et de la stabilité des calculs économiques.
- **Le rendu n'est qu'un consommateur** : si le rendu tourne à 30 FPS ou 144 FPS, la simulation produit exactement les mêmes résultats. Un mode `--headless` (simulation sans fenêtre) devient trivial — indispensable pour les tests automatisés et l'équilibrage en batch, exactement comme un backtest sans UI.
- **Pause = daemon en `sleep`** : l'UI reste interactive (consultation des panneaux), la simulation ne tick pas.

### 2.2 Écriture de l'état : le pattern Command

- **Règle absolue : rien n'écrit dans `GameState` sauf `Simulation.Tick()`.**
- L'UI et l'input ne modifient jamais l'état directement : ils poussent des `Command` (structs sérialisables : `DeclareWar(countryA, countryB)`, `SetTaxRate(country, 0.35)`) dans une file. Le tick suivant les valide puis les applique.
- Bénéfices identiques à une architecture d'ordres en trading :
  - **Validation centralisée** (un ordre invalide est rejeté à un seul endroit) ;
  - **Journal rejouable** (log des commandes + seed = replay complet d'une partie → débogage par bisection) ;
  - **Multijoueur possible plus tard** en lockstep (on n'échange que les commandes, pas l'état) ;
  - **L'IA des pays utilise la même API que le joueur** — pas de chemin de triche codé en dur.

### 2.3 State Management : base de données en mémoire, orientée tableaux

- **Un objet racine unique `GameState`** contient TOUT l'état mutable de la partie. Pas de singletons, pas de variables statiques, pas d'état caché dans des objets UI. Test de validité : *sérialiser `GameState` = sauvegarde complète et suffisante*.
- **Structure-of-Arrays (SoA) plutôt qu'objets** pour les entités nombreuses — pensez colonnes de séries temporelles, pas objets métier :

```csharp
// ANTI-PATTERN (POO naïve) : cache-misses massifs, GC pressure
class Province { Country owner; float infra; List<Building> b; ... }

// PATTERN RETENU : colonnes contiguës, itération linéaire cache-friendly
class ProvinceTable {
    public ushort[] OwnerId;        // index = provinceId
    public float[]  Infrastructure;
    public float[]  Manpower;
    public int[]    AdjacencyOffset; // graphe voisinage en CSR
    public ushort[] AdjacencyList;
}
```

- Justification : la passe économique quotidienne devient `for (int i = 0; i < N; i++)` sur des `float[]` — vectorisable, prévisible, ~zéro allocation. C'est le même raisonnement que vos calculs sur ticks : des buffers plats, pas des arbres d'objets.
- **IDs entiers partout** (`ushort provinceId`, `ushort countryId`), jamais de références objet croisées : sérialisation triviale, pas de cycles, lookups O(1).
- **Séparation stricte état chaud / données froides** :
  - `GameState` (mutable, sauvegardé) : propriétaires, stocks, armées, relations, dates.
  - `GameDefs` (immutable, chargé au boot depuis les fichiers de données, jamais sauvegardé) : définitions des bâtiments, lois, technologies, terrain. → Réf. section 4.
- **Le rendu lit l'état, ne le copie pas** (mono-thread au départ). Si la simulation est un jour déportée sur un thread dédié : publication de snapshots immutables par double-buffering (pattern identique à un feed de marché lock-free). **Ne pas multi-threader avant d'avoir profilé** — un tick bien écrit en SoA traite des centaines de pays en < 5 ms sur un cœur.

### 2.4 Ordre du tick (pipeline déterministe)

Chaque tick exécute des **systèmes** dans un ordre fixe et documenté — comme les étapes d'un pipeline de settlement :

```
Tick(state, commands):
  1. ApplyCommands        (ordres joueur + IA du tick précédent)
  2. EconomySystem        (production, commerce, taxes)
  3. LogisticsSystem      (ravitaillement, convois — graphe de flots)
  4. MilitarySystem       (mouvements, combats, attrition)
  5. PoliticsSystem       (lois, stabilité, diplomatie)
  6. AISystem             (les pays IA génèrent leurs Commands pour t+1)
  7. EventSystem          (déclencheurs scriptés — réf. section 4)
  8. state.Date += 1 tick
```

- Systèmes à **cadences différenciées** pour la performance : militaire à chaque tick (horaire), économie 1×/jour, diplomatie/IA lourde 1×/semaine, répartis en round-robin sur les pays pour lisser la charge (jamais 200 pays d'IA le même tick).
- **Déterminisme obligatoire** : un seul RNG seedé vivant dans `GameState`, aucune itération sur des collections à ordre non garanti (`Dictionary`) dans le code de simulation, aucune dépendance à l'horloge murale.

---

## 3. SYSTÈME DE CARTE GÉOGRAPHIQUE

### 3.1 Principe de la Color Map

La carte est une image `provinces.png` (ex. 8192×4096) où **chaque province est une zone de couleur RGB unique et uniforme** (méthode Paradox). La couleur est une **clé primaire visuelle**.

**Pipeline au chargement (une seule fois) :**
1. Charger le PNG **côté CPU** (`Raylib.LoadImage`) — jamais de lecture GPU par frame.
2. Parcourir tous les pixels ; construire `Dictionary<uint rgb, ushort provinceId>` en croisant avec `provinces.json` (réf. section 4) qui déclare `couleur ↔ id ↔ nom`.
3. **Précompiler une lookup map** : un tableau `ushort[largeur × hauteur]` = ID de province par pixel. Toute la suite du jeu travaille sur ce tableau, plus jamais sur les couleurs. (~64 Mo pour 8192×4096 — acceptable ; sinon tuiler.)
4. Dériver automatiquement, puis **mettre en cache sur disque** (recalcul uniquement si hash du PNG change) :
   - **Graphe d'adjacence** : pour chaque pixel, si le voisin droit/bas a un ID différent → arête `(a, b)`. Stockage en CSR (réf. §2.3). C'est le graphe utilisé par la logistique et les mouvements militaires (Dijkstra/A*).
   - **Centroïde** de chaque province (position des labels, icônes d'armées).
   - **Bounding box** de chaque province (culling, zoom-to-province).
   - **Frontières** : liste des pixels frontière, transformée en lignes pour le rendu.

### 3.2 Rendu : ID map + palette (le cœur de la performance graphique)

**Ne jamais redessiner province par province.** Rendu en 2 textures + 1 shader :

- **Texture A (statique)** : la province map encodée en ID (R+G = provinceId sur 16 bits), uploadée une fois.
- **Texture B (dynamique, minuscule)** : une palette 1D de `N_provinces` pixels — `palette[provinceId] = couleur d'affichage`. C'est la **seule** chose mise à jour quand la situation politique change (`UpdateTexture`, quelques Ko).
- **Fragment shader** (GLSL ~10 lignes, supporté nativement par Raylib) : lit l'ID dans A, échantillonne la couleur dans B.
- **Changer de map mode** (politique / terrain / économie / ravitaillement) = recalculer le tableau `palette[]` côté CPU (une boucle sur N provinces) et ré-uploader Texture B. Coût quasi nul, résultat instantané — c'est ainsi qu'un pays entier change de couleur en une frame lors d'une annexion.
- Couches au-dessus (frontières, fleuves, relief) : textures statiques dessinées par-dessus avec alpha.

### 3.3 Pan / Zoom / Picking via Raylib

- **`Camera2D` de Raylib fait tout le travail** : `target` (pan), `zoom`, `offset`. La carte est dessinée entre `BeginMode2D(camera)` / `EndMode2D()` ; l'UI ImGui est dessinée après, hors caméra.
- **Pan** : drag clic-milieu/droit → `camera.target -= mouseDelta / camera.zoom` ; ou edge-scrolling.
- **Zoom vers le curseur** (obligatoire pour le confort) :

```csharp
Vector2 mouseWorldBefore = Raylib.GetScreenToWorld2D(mousePos, camera);
camera.zoom = Math.Clamp(camera.zoom * (1 + wheel * 0.1f), zMin, zMax);
Vector2 mouseWorldAfter  = Raylib.GetScreenToWorld2D(mousePos, camera);
camera.target += mouseWorldBefore - mouseWorldAfter; // le point sous le curseur reste fixe
```

- **Picking de province en O(1)** — c'est là que la Color Map paie :

```csharp
// 1. Si ImGui capture la souris (clic dans un panneau), ne PAS picker la carte
if (ImGui.GetIO().WantCaptureMouse) return;
// 2. Écran → monde → pixel de la map → lookup
Vector2 world = Raylib.GetScreenToWorld2D(mousePos, camera);
int px = (int)world.X, py = (int)world.Y;         // + clamp aux bornes
ushort id = lookupMap[py * mapWidth + px];        // tableau CPU du §3.1
```

  Aucun raycast, aucune géométrie, aucune lecture GPU : un accès tableau.
- **Wrap horizontal** (la Terre est un cylindre) : dessiner la carte 2 fois (offset ±largeur) quand la caméra approche du bord, et appliquer `px = ((px % w) + w) % w` au picking.
- **Sélection visuelle** : province survolée/sélectionnée = modification de son entrée dans `palette[]` (highlight) — gratuit avec l'architecture §3.2.
- **LOD par zoom** : labels et icônes filtrés par niveau de zoom ; frontières fines masquées en vue lointaine. Piloté par de simples seuils sur `camera.zoom`.

---

## 4. ORGANISATION DES DONNÉES (Data-Driven Design)

### 4.1 Règle d'or

**Le moteur (C#) ne connaît aucun pays, aucune loi, aucun événement.** Il ne connaît que des *schémas*. Tout le contenu vit dans des fichiers de données. Le C# est le kernel ; les données sont l'espace utilisateur.

### 4.2 Format : **JSON** (verdict motivé)

| Format | Verdict | Raison |
|---|---|---|
| **JSON** | ✅ **Retenu** | Format le mieux maîtrisé par les IA génératives ; validation par schéma ; diffs Git lisibles ; parsing natif .NET ; zéro code custom |
| Script custom type Paradox | ❌ Rejeté | Écrire un parseur + l'IA hallucine une syntaxe qu'elle ne connaît pas → double source de bugs |
| SQLite | ❌ Rejeté pour le contenu | Illisible en diff Git, pénible à générer par IA. ✅ Acceptable plus tard pour l'*historique statistique* d'une partie (graphiques temporels) |
| YAML | ❌ Rejeté | Indentation significative = classe d'erreurs IA supplémentaire ; ambiguïtés de typage |

- **Sauvegardes** : `GameState` sérialisé en JSON compressé (gzip). Lisible en debug, diffable entre deux ticks pour traquer une divergence — l'équivalent du diff de deux snapshots d'order book.

### 4.3 Arborescence

```
/data
  /map
    provinces.png            # la Color Map (source de vérité géographique)
    provinces.json           # [{id, color:"#3A7F00", name, terrain, ...}]
    adjacency_overrides.json # détroits, canaux (arêtes ajoutées/retirées à la main)
  /common
    countries/    fra.json, deu.json, ...   # 1 fichier = 1 pays
    buildings/    buildings.json
    laws/         economic.json, conscription.json, ...
    technologies/ industry.json, land_doctrine.json, ...
    resources/    resources.json
  /events
    fra_politics.json, global_economy.json, ...
  /localisation
    fr.json, en.json          # aucune chaîne en dur dans le code
  /scenarios
    /1936/ bookmark.json, province_owners.json, armies.json, diplomacy.json
```

- **1 fichier = 1 sujet, fichiers courts** : une IA modifie `laws/economic.json` sans jamais toucher au reste → conflits et hallucinations minimisés, diffs Git ciblés.
- **Références par ID string** (`"building": "steel_mill"`), résolues en index entiers au chargement (interning) : les fichiers restent lisibles, le runtime reste rapide.

### 4.4 Exemples de schémas

```jsonc
// data/common/countries/fra.json
{
  "id": "FRA",
  "name_key": "country_fra",
  "color": "#3B6EC4",
  "capital_province": 3005,
  "government": "republic",
  "laws": { "economic": "civilian_economy", "conscription": "volunteer_only" },
  "starting_stats": { "stability": 0.55, "political_power": 50 }
}
```

```jsonc
// data/events/fra_politics.json — triggers/effects = petit vocabulaire fermé,
// interprété par l'EventSystem (§2.4). PAS un langage de script généraliste.
{
  "id": "fra_political_crisis_1",
  "trigger": { "all": [
    { "country_is": "FRA" },
    { "stat_below": ["stability", 0.3] },
    { "date_after": "1936-06-01" }
  ]},
  "mtth_days": 30,
  "options": [
    { "key": "opt_repress", "effects": [{ "add_stat": ["stability", 0.10] },
                                        { "add_stat": ["war_support", -0.05] }] },
    { "key": "opt_concede", "effects": [{ "add_stat": ["political_power", -25] }] }
  ]
}
```

- Le vocabulaire de conditions/effets (`stat_below`, `add_stat`, `country_is`…) est un **DSL fermé sur JSON** : assez expressif pour du contenu riche, assez contraint pour être validé mécaniquement — et pour que l'IA ne puisse pas inventer d'opérateurs sans être rejetée au chargement.

### 4.5 Validation : le loader est un firewall

- **Chargement fail-fast au boot** : ID dupliqué, couleur absente du PNG, référence pendante (`"steel_mil"` au lieu de `"steel_mill"`), stat hors bornes → **message d'erreur précis (fichier + champ) et arrêt**. Jamais de valeur par défaut silencieuse.
- Ces messages d'erreur sont conçus pour être **recollés tels quels dans un prompt** : l'IA corrige le fichier fautif sans contexte supplémentaire.
- **JSON Schemas** versionnés dans `/data/schemas/` : contrat lisible par l'IA (à inclure dans les prompts de génération de contenu), validation CI, autocomplétion éditeur.
- **Hot reload** (F5 recharge `/data` sans relancer la partie) : boucle de fer pour l'équilibrage et la production de contenu — l'équivalent du redémarrage à chaud d'un service systemd sans reboot de l'hyperviseur.

---

## 5. WORKFLOW DE DÉVELOPPEMENT ASSISTÉ PAR IA

### 5.1 Structure du dépôt Git

```
/gsg
  CLAUDE.md                  # contrat permanent lu par l'IA à chaque session (voir §5.2)
  /docs
    architecture_moteur_gsg.md   # CE document — la constitution du projet
    /adr/                        # Architecture Decision Records (1 fichier/décision)
  /src
    /Core/        GameState.cs, GameDefs.cs, Commands.cs, Tick.cs
    /Systems/     EconomySystem.cs, MilitarySystem.cs, ...  # 1 système = 1 fichier
    /Map/         ColorMapLoader.cs, MapRenderer.cs, Picking.cs, Camera.cs
    /UI/          1 panneau = 1 fichier (TradePanel.cs, ArmyPanel.cs, ...)
    /Data/        Loaders + validation (le firewall du §4.5)
    /App/         Program.cs, GameLoop.cs   # seul endroit qui référence Raylib+ImGui ensemble
  /tests
    /Core.Tests/  /Systems.Tests/  /Data.Tests/   # AUCUNE dépendance à Raylib
  /data           # réf. section 4
  /tools          # scripts one-shot (validation map, gen adjacence, stats de balance)
```

- **Frontière stricte** : `Core/`, `Systems/`, `Data/` ne référencent **jamais** Raylib ni ImGui (à faire respecter par la structure des projets .csproj, pas par la discipline). Conséquence : toute la simulation est testable et exécutable en headless — c'est votre garantie anti-régression pendant que l'IA génère du code.
- **Branches courtes, 1 branche = 1 feature**, merge sur `main` uniquement si `dotnet build` + `dotnet test` passent (CI GitHub Actions dès la semaine 1 — c'est votre métier, capitalisez dessus).

### 5.2 `CLAUDE.md` : le contrat permanent de l'IA

Fichier à la racine, lu automatiquement à chaque session. Contenu type :

```markdown
- Lire docs/architecture_moteur_gsg.md avant toute modification structurelle.
- INTERDIT : écrire dans GameState hors de Simulation.Tick() ; toute action passe par une Command.
- INTERDIT : référencer Raylib/ImGui dans Core/, Systems/, Data/.
- INTERDIT : DateTime.Now, Guid.NewGuid, Random non-seedé dans la simulation (déterminisme).
- Entités nombreuses : Structure-of-Arrays + IDs entiers (voir §2.3 du TDD).
- Tout nouveau contenu de jeu = fichiers dans /data, jamais de valeurs en dur dans le code.
- Commandes : build `dotnet build`, tests `dotnet test`, run `dotnet run --project src/App`.
- Après chaque feature : compiler, lancer les tests, corriger avant de conclure.
```

### 5.3 SOP : cycle de production d'une feature (étape par étape)

1. **Spécifier (humain)** — 5–15 lignes dans un fichier `docs/specs/NNN_feature.md` : quoi, entrées/sorties, critères d'acceptation. Vous savez rédiger un ticket d'incident ; c'est le même exercice.
2. **Plan d'abord (IA, sans écrire de code)** — *« Lis le TDD et la spec NNN. Propose un plan : fichiers touchés, signatures, structures de données. N'écris pas encore le code. »* → Vous validez le plan **avant** génération. 80% des dérives architecturales s'attrapent ici.
3. **Interfaces & tests avant implémentation** — faire générer d'abord les signatures + les tests unitaires (cas nominaux, bords, invariants : « la masse monétaire mondiale est conservée par le commerce », « un tick avec 0 commande ne modifie que la date »). Les tests sont le harnais qui contraint l'implémentation qui suit.
4. **Implémentation par petits lots** — 1 à 3 fichiers par prompt, jamais « implémente tout le système économique ». Toujours fournir : la spec, les fichiers existants concernés (contenu réel, pas de mémoire), le schéma JSON si du contenu est en jeu.
5. **Boucle de vérification mécanique** — `dotnet build` + `dotnet test` après chaque lot ; recoller les erreurs *verbatim* à l'IA. Ne jamais accepter de code non compilé « à relire plus tard ».
6. **Review humaine ciblée** — vous ne relisez pas tout : vous vérifiez les **invariants d'architecture** (écritures d'état hors tick ? allocation dans le hot path ? Raylib dans Core ? valeurs en dur qui devraient être dans /data ?). Checklist fixe, 5 minutes.
7. **Commit atomique** — message = référence à la spec. Puis mise à jour d'un `docs/adr/` si une décision structurelle a été prise.

### 5.4 Règles anti-hallucination / anti-dette

- **Contexte réel, pas supposé** : ne jamais laisser l'IA « imaginer » le contenu d'un fichier existant — le fournir. L'hallucination n°1 est l'API inventée sur du code non montré.
- **Le compilateur et le loader sont vos juges de paix** : toute sortie IA passe par `build → test → boot avec validation /data`. Une hallucination qui ne franchit pas ce pipeline ne coûte rien ; d'où l'importance d'avoir investi dans le firewall du §4.5 très tôt.
- **Une session IA = un objectif** ; les longues sessions multi-sujets dégradent la cohérence. Nouvelle feature → nouvelle session avec le TDD + la spec en contexte.
- **Interdire les refactors opportunistes** : exiger que l'IA ne touche qu'aux fichiers du plan validé (étape 2). Les refactors sont des specs à part entière, planifiées, avec les tests comme filet.
- **Budget dette explicite** : tout `// TODO` généré par l'IA doit être converti en issue Git ou supprimé au commit. Un TODO invisible est de la dette non provisionnée.
- **Profiler avant d'optimiser** : exiger des implémentations simples et correctes d'abord ; optimiser uniquement sur mesure (`--headless` + Stopwatch par système du §2.4, dashboard des temps de tick — vous savez faire du monitoring, instrumentez votre propre moteur).

### 5.5 Ordre de construction recommandé (jalons)

1. **M0 — Fenêtre + carte** : chargement Color Map, lookup, pan/zoom, picking, affichage nom de la province cliquée. *(Valide toute la section 3.)*
2. **M1 — Boucle & état** : `GameState`, tick fixe, vitesse/pause, date affichée, sauvegarde/chargement JSON. *(Valide la section 2.)*
3. **M2 — Data pipeline** : loader + validation + hot reload ; pays chargés depuis `/data`, map mode politique via palette. *(Valide la section 4.)*
4. **M3 — Premier système** : économie minimale (production/taxes) + premier panneau ImGui (table triable par pays). *(Valide la chaîne complète data → simulation → UI.)*
5. **M4 — Headless + CI + tests de déterminisme** (même seed + mêmes commandes = même hash d'état après 10 000 ticks).
6. **M5+** — militaire, logistique (le graphe d'adjacence devient un problème de flots — votre terrain), diplomatie, événements, IA des pays. Chaque système suit la SOP §5.3.

> **Le mot de la fin** : votre inexpérience en game dev n'est pas un handicap ici — les GSG sont le genre le plus proche d'un système d'information temps réel. Traitez ce moteur comme vous traiteriez un daemon critique : état centralisé, écritures contrôlées, déterminisme, instrumentation, validation en entrée. Le "jeu" n'est que le dashboard.
