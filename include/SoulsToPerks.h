#pragma once

// Souls to Perks - core. Dragon souls are the actor value kDragonSouls; perk points are the
// game's own perkCount byte (GameStateData). Both are saved BY THE GAME, so no serialization
// is needed - a conversion just moves value from one to the other on the main thread.

#include <cstdint>

namespace SoulsToPerks
{
	// Starts the low-rate tick used only for bAutoConvert. Call once at kDataLoaded.
	void Install();

	// Converts up to a_points perk points' worth of souls (main-thread only). Returns how
	// many points were actually granted (0 when souls are short or the cap would overflow).
	int Convert(int a_points);

	// Queues Convert(1) onto the main thread (safe from any thread).
	void RequestConvertOne();

	struct State
	{
		bool ticking = false;
		float dragonSouls = 0.0F;
		std::int8_t perkPoints = 0;
		std::uint64_t converted = 0;  // lifetime points granted this session
	};
	State GetState();
}
