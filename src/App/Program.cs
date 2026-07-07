using ImGuiNET;
using Raylib_cs;
using rlImGui_cs;

namespace App;

internal static class Program
{
    private const int WindowWidth = 1280;
    private const int WindowHeight = 720;
    private const string WindowTitle = "GSG Engine - M0";

    // Cap de rendu uniquement : la Frame n'a aucun rôle de simulation (Cdt 4, Tick ≠ Frame).
    private const int TargetFps = 60;

    private static readonly Color BackgroundColor = new Color(30, 30, 30, 255);

    private static void Main()
    {
        Raylib.InitWindow(WindowWidth, WindowHeight, WindowTitle);
        Raylib.SetTargetFPS(TargetFps);
        rlImGui.Setup(darkTheme: true);

        while (!Raylib.WindowShouldClose())
        {
            Raylib.BeginDrawing();
            Raylib.ClearBackground(BackgroundColor);

            rlImGui.Begin();
            ImGui.ShowDemoWindow();
            rlImGui.End();

            Raylib.EndDrawing();
        }

        rlImGui.Shutdown();
        Raylib.CloseWindow();
    }
}
