#include "PCH.h"

#include "DevBenchTool.h"

#include "DevBench/DevBenchAPI.h"
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
							player->AsActorValueOwner()->ModActorValue(RE::ActorValue::kDragonSouls, 5.0F);
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

			const auto s = SoulsToPerks::GetState();
			const std::string json = std::format(
				"{{\"ok\":true,"
				"\"settings\":{{\"soulsPerPoint\":{},\"autoConvert\":{},\"logLevel\":{},\"iniPath\":\"{}\"}},"
				"\"runtime\":{{\"ticking\":{},\"dragonSouls\":{:.1f},\"perkPoints\":{},\"converted\":{}}}}}",
				settings::general::soulsPerPoint, settings::general::autoConvert,
				settings::debug::logLevel, EscapeJson(settings::GetIniPath()),
				s.ticking, s.dragonSouls, static_cast<int>(s.perkPoints), s.converted);
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
			"lifetime conversions. op=grant adds 5 test souls; op=convert converts one point; "
			"op=reload re-reads the INI.\","
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
