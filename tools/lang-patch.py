# -*- coding: utf-8 -*-
"""lang-patch.py - one-shot, re-runnable language-support patch for Souls to Perks.

Applies the consumer-side mechanism from D:\\Claude output\\4. plans\\translation-rollout\\plan.md
sections 2 and 4.1: strings::TR() routing for every literal the settings page draws, the
"!ApocryphaMenuFramework" module-name lookup, strings::Configure() at kDataLoaded, and a
"strings" DevBench op. Every edit below is a must-match anchor replace: if an anchor is not
found EXACTLY ONCE the script raises instead of silently doing nothing, so a stale run against
changed source fails loudly rather than leaving the code half patched.

Run from anywhere: `python tools/lang-patch.py` (paths are relative to the repo root, taken as
this script's grandparent directory).
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(path, "r", encoding="utf-8", newline=None) as f:
        return f.read()


def write(path, text, crlf=False):
    with open(path, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as f:
        f.write(text)


def apply_one(text, anchor, replacement, label, done_marker=None):
    if done_marker is not None and done_marker in text:
        return text
    n = text.count(anchor)
    if n != 1:
        raise RuntimeError("[{}] anchor found {} time(s), expected exactly 1:\n{!r}".format(label, n, anchor))
    return text.replace(anchor, replacement, 1)


# ------------------------------------------------------------------------------------------------
# 1) include/SKSEMenuFramework.h - "!ApocryphaMenuFramework" first, ahead of the alias name.
# ------------------------------------------------------------------------------------------------
def patch_skse_menu_framework_h():
    path = os.path.join(REPO, "include", "SKSEMenuFramework.h")
    text = read(path)
    if 'GetModuleHandleW(L"!ApocryphaMenuFramework")' in text:
        return  # already applied by a previous (partial) run
    anchor = (
        "inline HMODULE GetMenuFrameworkModule() {\n"
        "    static HMODULE menuFramework = nullptr;\n"
        "    if (!menuFramework) {\n"
        "        menuFramework = GetModuleHandleW(L\"ApocryphaMenuFramework\");\n"
        "        if (!menuFramework) {\n"
        "            menuFramework = GetModuleHandleW(L\"SKSEMenuFramework\");\n"
        "        }\n"
        "    }\n"
        "    return menuFramework;\n"
        "}"
    )
    replacement = (
        "inline HMODULE GetMenuFrameworkModule() {\n"
        "    static HMODULE menuFramework = nullptr;\n"
        "    if (!menuFramework) {\n"
        "        menuFramework = GetModuleHandleW(L\"!ApocryphaMenuFramework\");\n"
        "        if (!menuFramework) {\n"
        "            menuFramework = GetModuleHandleW(L\"ApocryphaMenuFramework\");\n"
        "        }\n"
        "        if (!menuFramework) {\n"
        "            menuFramework = GetModuleHandleW(L\"SKSEMenuFramework\");\n"
        "        }\n"
        "    }\n"
        "    return menuFramework;\n"
        "}"
    )
    text = apply_one(text, anchor, replacement, "SKSEMenuFramework.h:GetMenuFrameworkModule")
    write(path, text, crlf=True)


# ------------------------------------------------------------------------------------------------
# 2) source/main.cpp - strings::Configure("SoulsToPerks") at kDataLoaded.
# ------------------------------------------------------------------------------------------------
def patch_main_cpp():
    path = os.path.join(REPO, "source", "main.cpp")
    text = read(path)
    if 'strings::Configure("SoulsToPerks")' in text:
        return  # already applied by a previous (partial) run

    text = apply_one(
        text,
        "#include \"UI.h\"\n\n#include \"utils/Logger.h\"",
        "#include \"UI.h\"\n\n#include \"utils/Logger.h\"\n#include \"utils/Strings.h\"",
        "main.cpp:include",
    )

    anchor = (
        "\t\tcase SKSE::MessagingInterface::kDataLoaded:\n"
        "\t\t\tUI::Register();\n"
        "\t\t\tSoulsToPerks::Install();\n"
        "\t\t\tDragonstone::Install();\n"
        "\t\t\tDevBenchTool::Init(true);\n"
        "\t\t\tbreak;"
    )
    replacement = (
        "\t\tcase SKSE::MessagingInterface::kDataLoaded:\n"
        "\t\t\tstrings::Configure(\"SoulsToPerks\");\n"
        "\t\t\tUI::Register();\n"
        "\t\t\tSoulsToPerks::Install();\n"
        "\t\t\tDragonstone::Install();\n"
        "\t\t\tDevBenchTool::Init(true);\n"
        "\t\t\tbreak;"
    )
    text = apply_one(text, anchor, replacement, "main.cpp:kDataLoaded")
    write(path, text, crlf=True)


# ------------------------------------------------------------------------------------------------
# 3) source/DevBenchTool.cpp - a "strings" op returning strings::StatusJson(); descriptor updated.
# ------------------------------------------------------------------------------------------------
def patch_devbench_tool_cpp():
    path = os.path.join(REPO, "source", "DevBenchTool.cpp")
    text = read(path)

    text = apply_one(
        text,
        "#include \"SoulsToPerks.h\"\n#include \"utils/Logger.h\"\n",
        "#include \"SoulsToPerks.h\"\n#include \"utils/Logger.h\"\n#include \"utils/Strings.h\"\n",
        "DevBenchTool.cpp:include",
    )

    anchor = (
        "\t\t\tif (has(\"reload\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tconst bool ok = settings::Reload();\n"
        "\t\t\t\ta_write(a_sink, std::format(R\"({{\"ok\":{},\"op\":\"reload\"}})\", ok ? \"true\" : \"false\").c_str());\n"
        "\t\t\t\treturn;\n"
        "\t\t\t}\n"
    )
    replacement = (
        "\t\t\tif (has(\"reload\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tconst bool ok = settings::Reload();\n"
        "\t\t\t\ta_write(a_sink, std::format(R\"({{\"ok\":{},\"op\":\"reload\"}})\", ok ? \"true\" : \"false\").c_str());\n"
        "\t\t\t\treturn;\n"
        "\t\t\t}\n"
        "\t\t\tif (has(\"strings\"))\n"
        "\t\t\t{\n"
        "\t\t\t\ta_write(a_sink, std::format(R\"({{\"ok\":true,\"op\":\"strings\",\"strings\":{}}})\", strings::StatusJson()).c_str());\n"
        "\t\t\t\treturn;\n"
        "\t\t\t}\n"
    )
    text = apply_one(text, anchor, replacement, "DevBenchTool.cpp:ControlTool ops")

    text = apply_one(
        text,
        "\"(0=1 point, 1=5, 2=10, 3=cancel); op=reload re-reads the INI.\\\",\"",
        "\"(0=1 point, 1=5, 2=10, 3=cancel); op=reload re-reads the INI; op=strings reports the active "
        "language, source and loaded translation count.\\\",\"",
        "DevBenchTool.cpp:descriptor",
    )
    write(path, text, crlf=True)


# ------------------------------------------------------------------------------------------------
# 4) source/UI.cpp - route every drawn literal through strings::TR().
# ------------------------------------------------------------------------------------------------
def patch_ui_cpp():
    path = os.path.join(REPO, "source", "UI.cpp")
    text = read(path)

    text = apply_one(
        text,
        "#include \"utils/Logger.h\"\n#include \"utils/Toggle.h\"",
        "#include \"utils/Logger.h\"\n#include \"utils/Strings.h\"\n#include \"utils/Toggle.h\"",
        "UI.cpp:include",
    )

    text = apply_one(
        text,
        "#include <algorithm>\n#include <functional>\n#include <string>",
        "#include <algorithm>\n#include <functional>\n#include <string>\n#include <vector>",
        "UI.cpp:vector include",
    )

    # --- kLogLevelNames block: add the parallel key array right after it --------------------------
    text = apply_one(
        text,
        "\t\tconstexpr const char* kLogLevelNames[] = { \"Trace\", \"Debug\", \"Info\", \"Warning\", \"Error\", \"Critical\", \"Off\" };\n"
        "\t\tconstexpr int kLogLevelCount = 7;",
        "\t\tconstexpr const char* kLogLevelNames[] = { \"Trace\", \"Debug\", \"Info\", \"Warning\", \"Error\", \"Critical\", \"Off\" };\n"
        "\t\tconstexpr const char* kLogLevelKeys[] = { \"STP_LogLevel_Trace\", \"STP_LogLevel_Debug\", \"STP_LogLevel_Info\",\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t\"STP_LogLevel_Warning\", \"STP_LogLevel_Error\", \"STP_LogLevel_Critical\", \"STP_LogLevel_Off\" };\n"
        "\t\tconstexpr int kLogLevelCount = 7;",
        "UI.cpp:kLogLevelKeys",
    )

    # --- HelpMarker: the "(?)" indicator (the tooltip text passed in is TR'd at each call site) ---
    text = apply_one(
        text,
        "\t\t\tImGuiMCP::SameLine();\n"
        "\t\t\tImGuiMCP::TextDisabled(\"(?)\");\n"
        "\t\t\tif (ImGuiMCP::IsItemHovered())\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::SetTooltip(\"%s\", a_description);\n"
        "\t\t\t}",
        "\t\t\tImGuiMCP::SameLine();\n"
        "\t\t\tImGuiMCP::TextDisabled(\"%s\", strings::TR(\"STP_HelpMark\", \"(?)\"));\n"
        "\t\t\tif (ImGuiMCP::IsItemHovered())\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::SetTooltip(\"%s\", a_description);\n"
        "\t\t\t}",
        "UI.cpp:HelpMarker",
    )

    # --- RenderGeneralSection: title, status line, slider + help, convert button + status, toggle
    #     + help, Dragonstone status lines -------------------------------------------------------
    text = apply_one(
        text,
        "\t\t\tImGuiMCP::SeparatorText(\"Souls to perks\");\n"
        "\n"
        "\t\t\tconst auto s = SoulsToPerks::GetState();\n"
        "\t\t\tImGuiMCP::Text(\"Dragon souls: %.0f    Perk points: %d\", s.dragonSouls, static_cast<int>(s.perkPoints));\n"
        "\n"
        "\t\t\tfloat rate = static_cast<float>(general::soulsPerPoint);\n"
        "\t\t\tif (NudgeableSlider(\"Souls per point\", &rate, 1.0F, 10.0F, \"%.0f\", 1.0F))\n"
        "\t\t\t{\n"
        "\t\t\t\tgeneral::soulsPerPoint = static_cast<std::uint32_t>(rate + 0.5F);\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"How many dragon souls one perk point costs.\");\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(\"Convert one point\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tSoulsToPerks::RequestConvertOne();\n"
        "\t\t\t\tstatusMessage = \"Converting...\";\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Spends the souls and grants one perk point, if you have enough.\");\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(\"Convert automatically\", &general::autoConvert);\n"
        "\t\t\tHelpMarker(\"Whenever you have enough souls, they convert on their own. Off by default - spending souls is your call.\");\n"
        "\n"
        "\t\t\tconst auto d = Dragonstone::GetState();\n"
        "\t\t\tif (d.resolved)\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::TextWrapped(\"The Dragonstone stands in the High Hrothgar courtyard - activate it to exchange souls in the world.\");\n"
        "\t\t\t}\n"
        "\t\t\telse\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::TextWrapped(\"SoulsToPerks.esl is not loaded - the Dragonstone at High Hrothgar cannot exist. Enable it in your mod manager.\");\n"
        "\t\t\t}",
        "\t\t\tImGuiMCP::SeparatorText(strings::TR(\"STP_Title\", \"Souls to perks\"));\n"
        "\n"
        "\t\t\tconst auto s = SoulsToPerks::GetState();\n"
        "\t\t\tImGuiMCP::Text(strings::TR(\"STP_SoulsPerksStatus\", \"Dragon souls: %.0f    Perk points: %d\"), s.dragonSouls, static_cast<int>(s.perkPoints));\n"
        "\n"
        "\t\t\tfloat rate = static_cast<float>(general::soulsPerPoint);\n"
        "\t\t\tif (NudgeableSlider(strings::TR(\"STP_SoulsPerPoint\", \"Souls per point\"), &rate, 1.0F, 10.0F, \"%.0f\", 1.0F))\n"
        "\t\t\t{\n"
        "\t\t\t\tgeneral::soulsPerPoint = static_cast<std::uint32_t>(rate + 0.5F);\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"STP_HelpSoulsPerPoint\", \"How many dragon souls one perk point costs.\"));\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"STP_ConvertBtn\", \"Convert one point\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tSoulsToPerks::RequestConvertOne();\n"
        "\t\t\t\tstatusMessage = strings::TR(\"STP_StatusConverting\", \"Converting...\");\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"STP_HelpConvert\", \"Spends the souls and grants one perk point, if you have enough.\"));\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(strings::TR(\"STP_AutoConvert\", \"Convert automatically\"), &general::autoConvert);\n"
        "\t\t\tHelpMarker(strings::TR(\"STP_HelpAutoConvert\", \"Whenever you have enough souls, they convert on their own. Off by default - spending souls is your call.\"));\n"
        "\n"
        "\t\t\tconst auto d = Dragonstone::GetState();\n"
        "\t\t\tif (d.resolved)\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::TextWrapped(\"%s\", strings::TR(\"STP_DragonstoneResolved\", \"The Dragonstone stands in the High Hrothgar courtyard - activate it to exchange souls in the world.\"));\n"
        "\t\t\t}\n"
        "\t\t\telse\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::TextWrapped(\"%s\", strings::TR(\"STP_EslNotLoaded\", \"SoulsToPerks.esl is not loaded - the Dragonstone at High Hrothgar cannot exist. Enable it in your mod manager.\"));\n"
        "\t\t\t}",
        "UI.cpp:RenderGeneralSection",
    )

    # --- RenderDebugSection: SeparatorText + Combo label + option list + HelpMarker ---------------
    text = apply_one(
        text,
        "\t\t\tImGuiMCP::SeparatorText(\"Debug\");\n"
        "\n"
        "\t\t\tint level = static_cast<int>(debug::logLevel);\n"
        "\t\t\tlevel = std::clamp(level, 0, kLogLevelCount - 1);\n"
        "\t\t\tif (ImGuiMCP::Combo(\"Log level\", &level, kLogLevelNames, kLogLevelCount))\n"
        "\t\t\t{\n"
        "\t\t\t\tdebug::logLevel = static_cast<std::uint32_t>(level);\n"
        "\t\t\t\tApplyLogLevel();\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Applies immediately. The log is at Documents\\\\My Games\\\\Skyrim Special Edition\\\\SKSE\\\\SoulsToPerks.log.\");",
        "\t\t\tImGuiMCP::SeparatorText(strings::TR(\"STP_Debug\", \"Debug\"));\n"
        "\n"
        "\t\t\tint level = static_cast<int>(debug::logLevel);\n"
        "\t\t\tlevel = std::clamp(level, 0, kLogLevelCount - 1);\n"
        "\t\t\t// Rebuilt from TR'd entries every frame (plan 2.2); labelStore owns the translated\n"
        "\t\t\t// bytes for this call so the const char* pointers handed to Combo stay valid.\n"
        "\t\t\tstd::vector<std::string> logLevelLabelStore;\n"
        "\t\t\tlogLevelLabelStore.reserve(kLogLevelCount);\n"
        "\t\t\tfor (int i = 0; i < kLogLevelCount; ++i)\n"
        "\t\t\t{\n"
        "\t\t\t\tlogLevelLabelStore.push_back(strings::TR(kLogLevelKeys[i], kLogLevelNames[i]));\n"
        "\t\t\t}\n"
        "\t\t\tstd::vector<const char*> logLevelLabels;\n"
        "\t\t\tlogLevelLabels.reserve(logLevelLabelStore.size());\n"
        "\t\t\tfor (const auto& s : logLevelLabelStore) { logLevelLabels.push_back(s.c_str()); }\n"
        "\t\t\tif (ImGuiMCP::Combo(strings::TR(\"STP_LogLevel\", \"Log level\"), &level, logLevelLabels.data(), kLogLevelCount))\n"
        "\t\t\t{\n"
        "\t\t\t\tdebug::logLevel = static_cast<std::uint32_t>(level);\n"
        "\t\t\t\tApplyLogLevel();\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"STP_HelpLogLevel\", \"Applies immediately. The log is at Documents\\\\My Games\\\\Skyrim Special Edition\\\\SKSE\\\\SoulsToPerks.log.\"));",
        "UI.cpp:RenderDebugSection",
    )

    # --- RenderButtons: Save / Reload / Restore buttons, their HelpMarkers, status assignments ----
    text = apply_one(
        text,
        "\t\t\tif (ImGuiMCP::Button(\"Save\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = \"Saving...\";\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Save() ? \"Settings saved.\" : \"Could not write the INI. See the log for why.\";\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Writes every setting on this page to the plugin's INI so it survives a restart.\");\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(\"Reload from INI\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = \"Reloading...\";\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Reload() ? \"Settings reloaded from the INI.\"\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t   : \"Could not read the INI. See the log for why.\";\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Throws away any change made here since the last save and re-reads the INI from disk.\");\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(\"Restore defaults\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tsettings::RestoreDefaults();\n"
        "\t\t\t\t\tlogger::debug(\"Restored default settings\");\n"
        "\t\t\t\t});\n"
        "\t\t\t\tstatusMessage = \"Defaults restored. Press Save to keep them.\";\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Puts every setting back to its fresh-install value. Nothing is written until you press Save.\");",
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"STP_SaveBtn\", \"Save\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = strings::TR(\"STP_StatusSaving\", \"Saving...\");\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Save() ? strings::TR(\"STP_StatusSaved\", \"Settings saved.\")\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t   : strings::TR(\"STP_StatusSaveFail\", \"Could not write the INI. See the log for why.\");\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"STP_HelpSave\", \"Writes every setting on this page to the plugin's INI so it survives a restart.\"));\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"STP_ReloadBtn\", \"Reload from INI\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = strings::TR(\"STP_StatusReloading\", \"Reloading...\");\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Reload() ? strings::TR(\"STP_StatusReloaded\", \"Settings reloaded from the INI.\")\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t   : strings::TR(\"STP_StatusReloadFail\", \"Could not read the INI. See the log for why.\");\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"STP_HelpReload\", \"Throws away any change made here since the last save and re-reads the INI from disk.\"));\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"STP_RestoreBtn\", \"Restore defaults\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tsettings::RestoreDefaults();\n"
        "\t\t\t\t\tlogger::debug(\"Restored default settings\");\n"
        "\t\t\t\t});\n"
        "\t\t\t\tstatusMessage = strings::TR(\"STP_StatusRestored\", \"Defaults restored. Press Save to keep them.\");\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"STP_HelpRestore\", \"Puts every setting back to its fresh-install value. Nothing is written until you press Save.\"));",
        "UI.cpp:RenderButtons",
    )

    # --- SettingsPanel::Render: strings::Tick() first, then the intro text ------------------------
    text = apply_one(
        text,
        "\tvoid __stdcall SettingsPanel::Render()\n"
        "\t{\n"
        "\t\tImGuiMCP::TextWrapped(\"Changes apply as soon as you make them. Press Save to keep them for the next time you play.\");",
        "\tvoid __stdcall SettingsPanel::Render()\n"
        "\t{\n"
        "\t\tstrings::Tick();\n"
        "\n"
        "\t\tImGuiMCP::TextWrapped(\"%s\", strings::TR(\"STP_Intro\", \"Changes apply as soon as you make them. Press Save to keep them for the next time you play.\"));",
        "UI.cpp:Render Tick+Intro",
    )

    write(path, text, crlf=True)


def main():
    patch_skse_menu_framework_h()
    patch_main_cpp()
    patch_devbench_tool_cpp()
    patch_ui_cpp()
    print("lang-patch.py: all anchors matched and patched.")


if __name__ == "__main__":
    main()
