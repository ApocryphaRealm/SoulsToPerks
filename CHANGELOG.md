# SoulsToPerks - changelog

Rule 61: this mod's own history, kept beside the code it describes.

<!-- VERSIONING-RULES -->
> **Versioning rules (CLAUDE.md rules 6 and 48):** `X.Y.Z`; a change increments the THIRD
> number; at `.9` the MINOR rolls. The next number is LAST WORKING + 1; failed/scratch/
> untested numbers are reused. Numbers come from version-ledger.ps1 + set-version.ps1.

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
