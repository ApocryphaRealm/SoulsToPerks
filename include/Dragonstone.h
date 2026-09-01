#pragma once

// The Dragonstone - the in-world way to spend souls. A placed activator in SoulsToPerks.esl
// (High Hrothgar courtyard); activating it opens a native exchange menu offering 1, 5 or 10
// perk points at the configured rate. The conversion itself is SoulsToPerks::Convert - this
// module only decides WHEN it runs.

#include <cstdint>

namespace Dragonstone
{
	// Resolves the placed reference from SoulsToPerks.esl and registers the activate sink.
	// Call at kDataLoaded. Safe to call again (no-op once resolved).
	void Install();

	// Opens the exchange menu (main thread only). What an activation does.
	void OpenExchangeMenu();

	// Applies a button choice: 0 = 1 point, 1 = 5 points, 2 = 10 points, 3 = cancel.
	// The menu's own callback routes here; the DevBench tool calls it directly.
	void Pick(std::uint32_t a_index);

	struct State
	{
		bool resolved = false;
		std::uint32_t refFormID = 0;   // runtime FormID of the placed reference (FExxx801)
		bool menuOpen = false;
		std::uint64_t activations = 0; // lifetime menu opens this session
	};
	State GetState();
}
