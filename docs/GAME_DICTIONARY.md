# GAME_DICTIONARY.md — Vocabulaire Ubiquitaire (Ubiquitous Language)
> **Statut : LOI.** Ces termes sont les **seuls** autorisés dans le code, les commentaires, les specs, les données et les réponses des agents.
> Un concept absent de ce fichier n'existe pas : le proposer à l'humain **avant** de l'employer, puis l'ajouter ici dans le même commit.
> Convention : terme canonique en **anglais dans le code**, définition en français.

---

## 1. TEMPS — la distinction la plus critique du projet

| Terme | Type C# | Définition stricte | Ne PAS confondre avec |
|---|---|---|---|
| **Tick** | `void Simulation.Tick(...)` / `ulong GameState.TickCount` | Pas de simulation **atomique, fixe et déterministe** = **1 heure de jeu**. Seul moment où `GameState` change. | `Frame`. Un tick n'a AUCUN lien avec l'écran. |
| **Frame** | boucle de rendu | Une itération de la boucle d'affichage (60–144 Hz, variable). Lit l'état, ne l'écrit jamais. | `Tick`. Interdiction d'utiliser `deltaTime` en simulation. |
| **GameDate** | `struct GameDate` | Date du monde (année/mois/jour/heure), **dérivée arithmétiquement de `TickCount`**. Jamais stockée à part, jamais liée à l'horloge machine. | `DateTime` (interdit en simulation). |
| **GameSpeed** | `enum GameSpeed` (Paused, S1…S5) | Nombre de ticks simulés par seconde réelle. `Paused` = 0 tick, UI toujours vivante. | Framerate. |
| **Cadence** | convention des Systems | Fréquence d'exécution d'un System : `Hourly` (chaque tick), `Daily`, `Weekly`. Répartie en round-robin sur les pays. | — |

> [!IMPORTANT]
> Le mot **« Update »** est **banni** du projet : dire `Tick` (simulation) ou `Draw` (rendu). Une méthode nommée `Update()` est un bug de vocabulaire.

## 2. ESPACE — carte et géographie

| Terme | Type C# | Définition stricte | Ne PAS confondre avec |
|---|---|---|---|
| **Province** | `ushort ProvinceId` | Unité géographique **atomique** : une zone de couleur unique dans `provinces.png`. Terrestre ou maritime. Tout est possédé/calculé à la maille province. | « Tile », « Cell », « Zone », « Territoire » — termes bannis. |
| **Region** | `ushort RegionId` | Groupe nommé de Provinces (théâtre, zone de ravitaillement). **Réservé** : ne pas l'implémenter sans spec dédiée. | `Province`, `Country`. |
| **ColorMap** | `provinces.png` | Image source où 1 couleur RGB unique = 1 Province. Source de vérité géographique, lue au boot uniquement. | Les textures de rendu. |
| **LookupMap** | `ushort[]` (w×h) | Tableau CPU précompilé `pixel → ProvinceId`. Sert au picking O(1). | `ColorMap` (la source), `Palette` (le rendu). |
| **AdjacencyGraph** | CSR (`int[] offsets`, `ushort[] neighbors`) | Graphe de voisinage des Provinces, dérivé de la ColorMap + `adjacency_overrides.json` (détroits, canaux). Support des pathfindings. | — |
| **Palette** | texture 1D, N provinces | Table `ProvinceId → couleur affichée`, seule texture mise à jour quand la carte change. | Couleurs d'identification de la ColorMap. |
| **MapMode** | `enum MapMode` | Vue thématique de la carte (Political, Terrain, Economic, Supply). Changer de MapMode = recalculer la Palette, rien d'autre. | — |
| **Picking** | `Picking.GetProvinceAt(...)` | Résolution `position écran → ProvinceId` via caméra + LookupMap. | Raycast (n'existe pas ici). |

## 3. ACTEURS ET ÉTAT — lever l'ambiguïté du mot « État »

> [!WARNING]
> Le mot français **« État »** est ambigu, donc **banni tel quel**. Deux concepts distincts, deux termes :

| Terme | Type C# | Définition stricte | Ne PAS confondre avec |
|---|---|---|---|
| **Country** | `ushort CountryId` | Entité **politique** jouable ou IA (France, Brésil…). Possède des Provinces, émet des Commands. | « Nation », « State », « Tag », « Puissance » — bannis. |
| **GameState** | `class GameState` (racine unique) | La **totalité de l'état mutable** de la partie : la « base de données en mémoire ». Sérialiser GameState = sauvegarde complète. Muté uniquement par `Tick()`. | `Country` (un acteur DANS l'état), `GameDefs`. |
| **GameDefs** | `class GameDefs` (immutable) | Définitions **immuables** chargées de `/data` au boot (bâtiments, lois, techs, terrain). Jamais sauvegardées, jamais mutées. | `GameState` (chaud/sauvé vs froid/rechargé). |
| **Scenario** | `/data/scenarios/1936/` | État initial d'une partie (bookmark) : propriétaires, armées, diplomatie au jour J. Sert à construire le GameState de départ. | `Save` (photo en cours de partie). |
| **Save** | JSON gzip de GameState | Snapshot sérialisé du GameState à un tick donné. | `Scenario`. |

## 4. SIMULATION — mécanique interne

| Terme | Type C# | Définition stricte | Ne PAS confondre avec |
|---|---|---|---|
| **System** | `sealed class XxxSystem` dans `src/Systems/` | Unité de logique de simulation appelée par `Tick()` dans un **ordre fixe**, à une Cadence donnée. Lit GameState/GameDefs, écrit GameState. | « Manager », « Service », « Engine », « Handler » — bannis comme noms de classes. |
| **Command** | `struct` sérialisable | **Ordre** émis par le joueur (UI) ou l'IA d'un Country, poussé en file, validé puis appliqué en début de tick. Unique porte d'écriture depuis l'extérieur. | `ScriptedEvent`. Une Command vient d'un acteur ; un event vient des données. |
| **CommandQueue** | file FIFO | File des Commands en attente du prochain tick. Journalisée (replay/debug). | — |
| **ScriptedEvent** | JSON dans `/data/events/` | Événement de contenu piloté par les données : `Trigger` + options + `Effects`. Évalué par l'EventSystem. | Les `event` C# (interdits en simulation) et les Commands. Ne jamais dire « Event » seul. |
| **Trigger** | vocabulaire JSON fermé | Condition d'un ScriptedEvent (`stat_below`, `country_is`, `date_after`…). Vocabulaire **fermé** : un opérateur inconnu = rejet au chargement. | — |
| **Effect** | vocabulaire JSON fermé | Mutation déclarative appliquée par l'EventSystem (`add_stat`…). Même règle de fermeture. | — |
| **Rng** | 1 instance seedée dans GameState | Unique source d'aléa de la simulation. Seed stockée en sauvegarde. | `System.Random` ad hoc (interdit). |
| **StateHash** | `ulong Hash(GameState)` | Empreinte du GameState, utilisée par les tests de déterminisme (2 runs même seed → même hash). | — |
| **Headless** | `--headless --ticks N` | Exécution de la simulation sans fenêtre ni rendu. Mode canonique des tests, benchs et CI. | — |

## 5. UI ET RENDU

| Terme | Type C# | Définition stricte | Ne PAS confondre avec |
|---|---|---|---|
| **Panel** | `sealed class XxxPanel` dans `src/UI/` | Fenêtre/panneau ImGui. **Lit** GameState, **émet** des Commands. 1 panel = 1 fichier. Peut garder un état d'affichage local (filtre, onglet), jamais de donnée de jeu. | « Window », « View », « Screen » — bannis. |
| **Draw** | `void Draw(...)` | La passe de rendu d'une Frame (carte puis panels). Lecture seule sur GameState. | `Tick`. |
| **Camera** | `Camera2D` Raylib | Pan/zoom de la carte. N'existe que côté rendu ; la simulation ignore la caméra. | — |
| **Topbar / Tooltip / Popup** | ImGui | Sens usuel ImGui. Mêmes règles que Panel. | — |

## 6. DONNÉES

| Terme | Type C# | Définition stricte | Ne PAS confondre avec |
|---|---|---|---|
| **Def** | entrées de GameDefs | Définition d'un type de contenu (`BuildingDef`, `LawDef`…) chargée depuis `/data/common/`. Immutable. | L'instance en jeu (compteur dans GameState). |
| **StringKey** | `string` dans les JSON | Identifiant lisible d'un Def (`"steel_mill"`). N'existe que dans les fichiers et les messages d'erreur. | L'ID runtime. |
| **Interning** | au chargement | Résolution `StringKey → ID entier` faite une fois par le Loader. Le runtime ne compare jamais de strings. | — |
| **Loader** | `src/Data/` | Pipeline de chargement + validation **fail-fast** de `/data`. C'est le firewall : il rejette avec fichier + champ + raison. | — |
| **Schema** | `/data/schemas/*.json` | Contrat JSON Schema d'un type de données. Fourni aux IA pour générer du contenu, utilisé en CI. | — |
| **HotReload** | F5 | Rechargement de `/data` en cours de partie, sans redémarrage. | — |

## 7. TYPES D'ID CANONIQUES

| ID | Type C# | Espace | Remarque |
|---|---|---|---|
| `ProvinceId` | `ushort` | 0 … ~65 000 | Index direct dans les tableaux SoA. |
| `CountryId` | `ushort` | 0 … ~1 000 | `0` = réservé « aucun / mer ». |
| `BuildingId`, `LawId`, `TechId`, `ResourceId` | `ushort` | par type | Issus de l'Interning des StringKeys. |
| `RegionId` | `ushort` | réservé | Ne pas utiliser sans spec. |

Règle : **jamais** d'`int` nu pour un ID, jamais de `string` comparée au runtime, jamais de `Guid`.

## 8. TABLE DES TERMES BANNIS (rappel rapide)

| ❌ Banni | ✅ Dire à la place |
|---|---|
| Update (méthode/concept) | `Tick` (simulation) ou `Draw` (rendu) |
| Nation, State, Tag, Puissance | `Country` |
| État (seul) | `GameState` (technique) ou `Country` (politique) |
| Tile, Cell, Zone, Territoire | `Province` |
| Event (seul) | `ScriptedEvent` ou `Command` selon le cas |
| Manager, Service, Helper, Util (noms de classes) | `XxxSystem`, `XxxPanel`, `XxxLoader` |
| deltaTime (en simulation) | n'existe pas : la simulation compte des Ticks |
