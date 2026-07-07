# SPEC 001 — Socle .NET + Raylib + ImGui (jalon M0)
> Statut : VALIDÉE — 2026-07-07 (GO humain reçu)
> Classe SOP : A

## Objectif
Créer la solution .NET 8 compilable qui ouvre une fenêtre Raylib avec la démo ImGui et se ferme proprement : preuve que toute la chaîne graphique (Raylib-cs + ImGui.NET + rlImGui-cs) fonctionne sur la machine cible.

## Périmètre
- **Inclus** : `gsg_engine.sln`, `src/App/App.csproj` (console .NET 8), `src/App/Program.cs`, `.gitignore`.
- **Exclus** (explicitement hors-scope) : `GameState`, `Simulation.Tick()`, `/data`, ColorMap, Camera, tout panneau UI custom, projet `/tests` (naîtra en M1 avec la première logique headless).

## Comportement attendu
- Entrées : aucune (pas d'arguments CLI dans cette spec).
- Sorties : fenêtre 1280×720 titrée « GSG Engine - M0 », fond gris foncé, fenêtre de démo ImGui interactive, 60 FPS cible.
- Règles : init Raylib → init rlImGui → boucle Frame (`BeginDrawing`, `ClearBackground`, `rlImGui.Begin`, `ImGui.ShowDemoWindow`, `rlImGui.End`, `EndDrawing`) → teardown dans l'ordre inverse (`rlImGui.Shutdown` puis `CloseWindow`).

## Critères d'acceptation (testables)
- [ ] `dotnet build` : 0 erreur, 0 warning (lint armé par `Directory.Build.props`)
- [ ] Lancement : la fenêtre s'affiche, la démo ImGui répond à la souris
- [ ] Fermeture par la croix : le process se termine sans exception (exit code 0)
- [ ] Aucun test xUnit : **dérogation actée** — 100 % du code de cette spec est graphique (interdit de test par convention) ; aucune logique de simulation n'existe encore.

## Notes / risques
- Paquets épinglés par le restore local (`nuget.config` → `.packages/`) : Raylib-cs 8.0.0, ImGui.NET 1.91.6.1, rlImgui-cs 3.2.0. Décision de stack : TDD §1.1 (pas d'ADR supplémentaire).
- `App.csproj` généré par template : suppression de `<ImplicitUsings>` et `<Nullable>` locaux pour laisser `Directory.Build.props` gouverner (un csproj écrase les props).
