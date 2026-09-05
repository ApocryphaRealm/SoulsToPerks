#include "PCH.h"

#include "DevBenchTool.h"

#include "DevBench/DevBenchAPI.h"
#include "Dragonstone.h"
#include "Settings.h"
#include "SoulsToPerks.h"
#include "utils/Logger.h"

#include <format>
#include <string>
#include <string_view>

namespace DevBenchTool
{
	namespace
	{
		std::string EscapeJson(std::string_view a_in)
		{
			std::string out;
			out.reserve(a_in.size() + 8);
			for (const char c : a_in)
			{
				switch (c)
				{
				case '\\': out += "\\\\"; break;
				case '"': out += "\\\""; break;
				case '\n': out += "\\n"; break;
				default: out += c; break;
				}
			}
			return out;
		}

		void ControlTool(void*, const char* a_argsJson, void* a_sink, DevBenchAPI::WriteFn a_write)
		{
			const std::string_view args = a_argsJson ? a_argsJson : "";
			auto has = [&](const char* a_op) { return args.find(std::format("\"{}\"", a_op)) != std::string_view::npos; };

			if (has("grant"))
			{
				// Test drive: +5 dragon souls, main-thread queued.
				if (auto* tasks = SKSE::GetTaskInterface())
				{
					tasks->AddTask([]() {
						if (auto* player = RE::PlayerCharacter::GetSingleton())
						{
							#if RUNTIME_LINE == 17
							player->AsActorValueOwner()->ModBaseActorValue(RE::ActorValue::kDragonSouls, 5.0F);
#else
							player->AsActorValueOwner()->ModActorValue(RE::ActorValue::kDragonSouls, 5.0F);
#endif
						}
					});
				}
				a_write(a_sink, R"({"ok":true,"op":"grant","souls":5})");
				return;
			}
			if (has("convert"))
			{
				SoulsToPerks::RequestConvertOne();
				a_write(a_sink, R"({"ok":true,"op":"convert"})");
				return;
			}
			if (has("reload"))
			{
				const bool ok = settings::Reload();
				a_write(a_sink, std::format(R"({{"ok":{},"op":"reload"}})", ok ? "true" : "false").c_str());
				return;
			}
			if (has("activate"))
			{
				// Test drive: open the Dragonstone exchange menu exactly as an activation would.
				if (auto* tasks = SKSE::GetTaskInterface()) { tasks->AddTask([]() { Dragonstone::OpenExchangeMenu(); }); }
				a_write(a_sink, R"({"ok":true,"op":"activate"})");
				return;
			}
			if (has("touch"))
			{
				// Test drive through the ENGINE path: ActivateRef on the placed reference is what
				// the player's activate key ends in, and it raises TESActivateEvent for our sink.
				if (auto* tasks = SKSE::GetTaskInterface())
				{
					tasks->AddTask([]() {
						auto* player = RE::PlayerCharacter::GetSingleton();
						const auto d = Dragonstone::GetState();
						auto* form = d.refFormID ? RE::TESForm::LookupByID(d.refFormID) : nullptr;
						auto* ref = form ? form->AsReference() : nullptr;
						if (player && ref) { ref->ActivateRef(player, 0, nullptr, 1, false); }
						else { logger::warn("touch: Dragonstone reference 0x{:08X} is not loaded (stand in its cell first)", d.refFormID); }
					});
				}
				a_write(a_sink, R"({"ok":true,"op":"touch"})");
				return;
			}
			for (std::uint32_t i = 0; i < 4; ++i)
			{
				// op=pick:N applies button N of the open exchange menu (0 = 1 point, 1 = 5, 2 = 10, 3 = cancel).
				if (has(std::format("pick:{}", i).c_str()))
				{
					if (auto* tasks = SKSE::GetTaskInterface()) { tasks->AddTask([i]() { Dragonstone::Pick(i); }); }
					a_write(a_sink, std::format(R"({{"ok":true,"op":"pick","index":{}}})", i).c_str());
					return;
				}
			}

			auto s = SoulsToPerks::GetState();
			if (auto* player = RE::PlayerCharacter::GetSingleton())
			{
				// Live numbers for the driver, whatever the pause state (the tick skips in menus).
				s.dragonSouls = player->AsActorValueOwner()->GetActorValue(RE::ActorValue::kDragonSouls);
				s.perkPoints = player->GetGameStatsData().perkCount;
			}
			const auto d = Dragonstone::GetState();
			const std::string json = std::format(
				"{{\"ok\":true,"
				"\"settings\":{{\"soulsPerPoint\":{},\"autoConvert\":{},\"logLevel\":{},\"iniPath\":\"{}\"}},"
				"\"runtime\":{{\"ticking\":{},\"dragonSouls\":{:.1f},\"perkPoints\":{},\"converted\":{},"
				"\"dragonstoneResolved\":{},\"dragonstoneRefId\":\"0x{:08X}\",\"menuOpen\":{},\"activations\":{}}}}}",
				settings::general::soulsPerPoint, settings::general::autoConvert,
				settings::debug::logLevel, EscapeJson(settings::GetIniPath()),
				s.ticking, s.dragonSouls, static_cast<int>(s.perkPoints), s.converted,
				d.resolved, d.refFormID, d.menuOpen, d.activations);
			a_write(a_sink, json.c_str());
		}
	}

	void Init(bool a_lastAttempt)
	{
		static bool registered = false;
		if (registered) { return; }

		DevBenchAPI::IDevBenchInterface001* devBench = DevBenchAPI::GetDevBenchInterface001();
		if (!devBench)
		{
			if (a_lastAttempt) { logger::info("DevBench not detected; skipping the \"stp.control\" tool"); }
			else { logger::debug("DevBench not detected yet; will retry at the next message"); }
			return;
		}

		constexpr const char* descriptor =
			"{"
			"\"description\":\"Souls to Perks live state: settings, dragon souls, perk points and "
			"lifetime conversions, Dragonstone reference. op=grant adds 5 test souls; op=convert converts one "
			"point; op=activate opens the Dragonstone exchange menu; op=touch activates the placed reference through the engine "
			"(its cell must be loaded); op=pick:N applies its button N "
			"(0=1 point, 1=5, 2=10, 3=cancel); op=reload re-reads the INI.\","
			"\"inputSchema\":{\"type\":\"object\",\"properties\":{\"op\":{\"type\":\"string\"}}},"
			"\"readOnly\":false"
			"}";

		if (devBench->RegisterTool("stp.control", descriptor, &ControlTool, nullptr))
		{
			logger::info("Registered \"stp.control\" with DevBench (build {})", devBench->GetBuildNumber());
			registered = true;
		}
	}
}
