# SoulsToPerks - changelog

Rule 61: this mod's own history, kept beside the code it describes.

<!-- VERSIONING-RULES -->
> **Versioning rules (CLAUDE.md rules 6 and 48):** `X.Y.Z`; a change increments the THIRD
> number; at `.9` the MINOR rolls. The next number is LAST WORKING + 1; failed/scratch/
> untested numbers are reused. Numbers come from version-ledger.ps1 + set-version.ps1.

## 1.0.7 - 2026-10-25 - working

### Fixed
- Dragon souls and perk points are read only once the player is placed in a cell, so the watcher, the Convert call, the Dragonstone menu and the DevBench readout never ask the player's actor values at the main menu, where the player exists with no character loaded.
- The Souls per point slider is a precise slider: a keyboard or D-pad nudge moves it by exactly one (rule 68; the package gate requires it from this update).
- The plugin no longer changes any vanilla record. Up to 1.0.6 it placed the Dragonstone through the plugin, which forced it to carry copies of the High Hrothgar courtyard cell and the Tamriel worldspace records (and the worldspace copy left out its max-height data); a mod that edits either could be undone by it depending on load order. SoulsToPerks.esp now holds one record, the Dragonstone activator, and overrides no cell, worldspace or placed reference.

### Changed
- The Dragonstone is placed in the High Hrothgar courtyard by the DLL when that cell loads, at the same spot, facing and size as before. The game keeps it in the save like any object placed at runtime, so later visits and reloads find it and place nothing new; a second stone, if one ever turns up, is removed. A save made with 1.0.6 simply gets the new stone on the next visit (the old placed reference left with the plugin record it came from).
- The message-box call no longer carries a VR address; the mod does not support VR.
- The DevBench readout reports the courtyard stone: its reference, how many stand there, how many this session placed and how many duplicates it removed.
- The plugin generator writes the one-record SoulsToPerks.esp with the light flag only.

## 1.0.6 - 2026-09-18 - untested

### Changed
- The Address Library pre-check runs before anything else at load: a missing Address Library file for the game version
  gets a message naming the file and the plugin loads inert, instead of CommonLibSSE-NG's bare failure line
  (oproso's report on the Perfected Wheeler page, 2026-09-18: a guard placed after SKSE::Init never ran). No other change.

## 1.0.5 - 2026-09-16 - untested

### Changed
- The plugin is now SoulsToPerks.esp, a light ESPFE. It also carried the ESM flag, which pinned it to the top of the load order regardless of extension; that is cleared. Saves referencing the old .esl will not find its records.

## 1.0.3 - 2026-09-07 - working

### Added
- The settings page is shown in the game's language: Japanese, Korean, Chinese, Russian, German, French, Spanish, Italian, Polish and Czech translation files ship beside the DLL (Interface/Translations/SoulsToPerks_<language>.txt) and the page follows the Apocrypha Menu Framework's Language setting; English is the fallback. The framework is looked up by its sort-first name first; stp.control gained op=strings.

## 1.0.2 - 2026-09-05 - untested

### Added
- Added a Skyrim 1.7.99 / 1.7.104 build; the mod now installs as a FOMOD that picks the build for your game version (SE 1.5.97 / AE 1.6.1170, or Skyrim 1.7.x).

## 1.0.1 - 2026-09-01 - working

### Added
- The Dragonstone is back as the in-world way to spend souls (design decision 2026-09-01),
  standing in the High Hrothgar courtyard. Activate it and an exchange menu offers 1, 5 or
  10 perk points at the configured rate, showing your souls and points; the settings page's
  Convert button and the automatic mode are unchanged.
- SoulsToPerks.esl: a two-record light plugin (the Dragonstone activator on the vanilla
  RuinsDragonStone01 mesh, and its placed reference) plus the structurally required Tamriel /
  HighHrothgarExterior01 parent overrides, authored by tools/Build-SoulsToPerksEsl.py. No
  script. The DLL resolves the reference and listens for TESActivateEvent on it.
- `stp.control` gains op=activate (opens the exchange menu), op=pick:N (applies button N)
  and reports the Dragonstone's runtime FormID.

## 1.0.0 - 2026-09-01 - working

### Added
- First release. Dragon souls convert into perk points at a configurable rate
  (uSoulsPerPoint, default 1 soul per point). Spending is explicit by default: the
  settings page shows souls and perk points live and has a "Convert one point" button.
  bAutoConvert (off by default) converts on its own whenever enough souls are banked.
- Both values are the game's own saved state (the DragonSouls actor value and the
  perk-point counter), so a conversion is a plain main-thread transfer - nothing to
  serialize, nothing to re-apply on load, nothing left behind on uninstall.
- AutoDraw-pattern core: a 1 Hz poster-thread tick (used only for auto-convert), no hooks,
  no relocations, no plugin file.
- In-game settings page (Apocrypha Menu Framework, stock SKSE Menu Framework fallback):
  souls/points readout, rate slider, Convert button, auto toggle, Save/Reload/Restore.
- Plain-file INI (redirector-proof), DevBench driving tool `stp.control`, .pdb debug
  symbols in the main download.
