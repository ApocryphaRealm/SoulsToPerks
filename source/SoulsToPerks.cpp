#include "PCH.h"

#include "SoulsToPerks.h"

#include "Settings.h"
#include "utils/Logger.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <mutex>
#include <thread>

namespace SoulsToPerks
{
	namespace
	{
		std::atomic<bool> g_installed{ false };
		std::atomic<bool> g_tickPending{ false };

		std::mutex g_stateLock;
		State g_state;

		void RefreshState(RE::PlayerCharacter* a_player, State& a_out)
		{
			a_out.dragonSouls = a_player->AsActorValueOwner()->GetActorValue(RE::ActorValue::kDragonSouls);
			a_out.perkPoints = a_player->GetGameStatsData().perkCount;
		}

		void Tick()
		{
			g_tickPending.store(false, std::memory_order_release);

			State s;
			s.ticking = true;

			auto* ui = RE::UI::GetSingleton();
			auto* player = RE::PlayerCharacter::GetSingleton();
			if (!ui || ui->GameIsPaused() || !player || !player->Is3DLoaded())
			{
				// Paused (a menu is up) or no player yet: keep the last real readout rather
				// than zeroing it - the settings page and message box read these values.
				std::scoped_lock l(g_stateLock);
				g_state.ticking = true;
				return;
			}

			RefreshState(player, s);

			if (settings::general::autoConvert)
			{
				const float cost = static_cast<float>(settings::general::soulsPerPoint);
				while (s.dragonSouls >= cost && s.perkPoints < 127)
				{
					if (Convert(1) != 1) { break; }
					RefreshState(player, s);
				}
			}

			std::scoped_lock l(g_stateLock);
			s.converted = g_state.converted;
			g_state = s;
		}
	}

	void Install()
	{
		if (g_installed.exchange(true)) { return; }
		if (!SKSE::GetTaskInterface())
		{
			g_installed = false;
			logger::error("SKSE task interface unavailable; the mod cannot run");
			return;
		}

		// Poster thread + pending flag (the AutoDraw pattern; a task must never re-queue
		// itself). 1 Hz is plenty - souls arrive at dragon-kill rate.
		std::thread([]() {
			while (g_installed.load(std::memory_order_relaxed))
			{
				if (!g_tickPending.exchange(true, std::memory_order_acq_rel))
				{
					if (auto* tasks = SKSE::GetTaskInterface()) { tasks->AddTask(Tick); }
					else { g_tickPending.store(false, std::memory_order_release); }
				}
				std::this_thread::sleep_for(std::chrono::milliseconds(1000));
			}
		}).detach();

		logger::info("tick poster installed (auto-convert watcher, 1 Hz)");
	}

	int Convert(int a_points)
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player || a_points <= 0) { return 0; }

		auto* avOwner = player->AsActorValueOwner();
		const float souls = avOwner->GetActorValue(RE::ActorValue::kDragonSouls);
		const std::uint32_t perSoul = std::max(1u, settings::general::soulsPerPoint);
		auto& stats = player->GetGameStatsData();

		int granted = 0;
		for (int i = 0; i < a_points; ++i)
		{
			const float cost = static_cast<float>(perSoul);
			const float have = souls - static_cast<float>(granted) * cost;
			if (have < cost || stats.perkCount >= 127) { break; }
			avOwner->ModActorValue(RE::ActorValue::kDragonSouls, -cost);
			stats.perkCount = static_cast<std::int8_t>(stats.perkCount + 1);
			++granted;
		}

		if (granted > 0)
		{
			std::scoped_lock l(g_stateLock);
			g_state.converted += static_cast<std::uint64_t>(granted);
			RefreshState(player, g_state);  // publish now - the tick skips while a menu pauses the game
			logger::info("converted {} dragon soul(s) into {} perk point(s) (rate {}:1)",
						 granted * perSoul, granted, perSoul);
		}
		return granted;
	}

	void RequestConvertOne()
	{
		if (auto* tasks = SKSE::GetTaskInterface())
		{
			tasks->AddTask([]() { Convert(1); });
		}
	}

	State GetState()
	{
		std::scoped_lock l(g_stateLock);
		return g_state;
	}
}
