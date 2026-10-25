#pragma once

// The Dragonstone - the in-world way to spend souls. An activator record in SoulsToPerks.esp,
// placed in the High Hrothgar courtyard at runtime by this module when that cell loads (the
// plugin itself places nothing and overrides no vanilla record); activating it opens a native
// exchange menu offering 1, 5 or 10 perk points at the configured rate. The conversion itself
// is SoulsToPerks::Convert - this module only decides WHEN it runs.

#include <cstdint>

namespace Dragonstone
{
	// Resolves the activator from SoulsToPerks.esp and registers the activate and cell-load sinks.
	// Call at kDataLoaded. Safe to call again (no-op once resolved).
	void Install();

	// After a save load or a new game: checks the courtyard once (it may already be loaded).
	void OnGameLoaded();

	// Opens the exchange menu (main thread only). What an activation does.
	void OpenExchangeMenu();

	// Applies a button choice: 0 = 1 point, 1 = 5 points, 2 = 10 points, 3 = cancel.
	// The menu's own callback routes here; the DevBench tool calls it directly.
	void Pick(std::uint32_t a_index);

	struct State
	{
		bool resolved = false;
		std::uint32_t refFormID = 0;         // runtime FormID of the courtyard stone (0 until seen this session)
		std::uint32_t courtyardCount = 0;    // stones standing in the courtyard after the last check
		std::uint32_t placements = 0;        // stones this session created
		std::uint32_t duplicatesRemoved = 0; // extra stones this session removed
		bool menuOpen = false;
		std::uint64_t activations = 0;       // lifetime menu opens this session
	};
	State GetState();
}
