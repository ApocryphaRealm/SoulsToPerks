#include "PCH.h"

#include "Dragonstone.h"

#include "Settings.h"
#include "SoulsToPerks.h"
#include "utils/Logger.h"

#include <algorithm>
#include <atomic>
#include <format>
#include <string>

#undef MessageBox

namespace RE
{
	// The game's own message-box opener (title, callback, options) - the same engine call the
	// project's Local Map Upgrade uses for its marker prompt, resolved through Address Library.
	std::uint32_t UI__OpenMessageBox(const BSString& a_title, const BSTSmartPointer<IMessageBoxCallback>& a_callback,
									 std::uint8_t a_arg3, std::uint32_t a_arg4, std::int32_t a_arg5,
									 const BSTArray<BSString>& a_options)
	{
		using func_t = decltype(&UI__OpenMessageBox);
		static REL::Relocation<func_t> func{ REL::VariantID(51421, REL::Module::get().version() < SKSE::RUNTIME_SSE_1_6_1130 ? 52270 : 442726, 0x8D82D0) };
		return func(a_title, a_callback, a_arg3, a_arg4, a_arg5, a_options);
	}
}

namespace Dragonstone
{
	namespace
	{
		// The contract with SoulsToPerks.esl (tools/Build-SoulsToPerksEsl.py):
		// 0x800 ACTI (the Dragonstone), 0x801 REFR (its placed reference at High Hrothgar).
		// The BASE form is what gets resolved: the placed reference is a temporary exterior
		// ref, and temporary refs only enter the form table while their cell is loaded, so a
		// LookupForm on 0x801 at kDataLoaded finds nothing. Matching the base object also
		// means any Dragonstone placed from this activator works, not just ours.
		constexpr const char* kPluginFileName = "SoulsToPerks.esl";
		constexpr RE::FormID kActivatorLocalFormID = 0x800;
		constexpr RE::FormID kRefLocalFormID = 0x801;
		constexpr std::uint32_t kPointsPerButton[] = { 1, 5, 10 };

		RE::TESBoundObject* g_acti = nullptr;
		bool g_sinkRegistered = false;
		std::atomic<bool> g_menuOpen{ false };
		std::atomic<std::uint64_t> g_activations{ 0 };

		struct ExchangeCallback : RE::IMessageBoxCallback
		{
#if RUNTIME_LINE == 17
			void Run(std::uint8_t a_optionIndex) override
			{
				Pick(static_cast<std::uint32_t>(a_optionIndex));
			}
#else
			void Run(Message a_optionIndex) override
			{
				Pick(static_cast<std::uint32_t>(a_optionIndex));
			}
#endif
		};

		class ActivateSink : public RE::BSTEventSink<RE::TESActivateEvent>
		{
		public:
			static ActivateSink* GetSingleton()
			{
				static ActivateSink singleton;
				return &singleton;
			}

			RE::BSEventNotifyControl ProcessEvent(const RE::TESActivateEvent* a_event, RE::BSTEventSource<RE::TESActivateEvent>*) override
			{
				if (!a_event || !g_acti || !a_event->objectActivated || a_event->objectActivated->GetBaseObject() != g_acti)
				{
					return RE::BSEventNotifyControl::kContinue;
				}
				auto* player = RE::PlayerCharacter::GetSingleton();
				if (!player || !a_event->actionRef || a_event->actionRef.get() != static_cast<RE::TESObjectREFR*>(player))
				{
					return RE::BSEventNotifyControl::kContinue;
				}
				logger::info("Dragonstone activated by the player");
				OpenExchangeMenu();
				return RE::BSEventNotifyControl::kContinue;
			}
		};
	}

	void Install()
	{
		if (g_sinkRegistered) { return; }

		auto* dataHandler = RE::TESDataHandler::GetSingleton();
		if (!dataHandler)
		{
			logger::warn("TESDataHandler unavailable at kDataLoaded; the Dragonstone cannot be resolved");
			return;
		}

		RE::TESForm* form = dataHandler->LookupForm(kActivatorLocalFormID, kPluginFileName);
		if (!form)
		{
			logger::error("{} is not in the load order - the Dragonstone at High Hrothgar cannot exist. "
						  "Souls can still be spent from the settings page.", kPluginFileName);
			return;
		}
		g_acti = form->As<RE::TESBoundObject>();
		if (!g_acti)
		{
			logger::error("{} 0x{:03X} resolved but is not a placeable object (type {})", kPluginFileName, kActivatorLocalFormID,
						  static_cast<int>(form->GetFormType()));
			return;
		}

		auto* holder = RE::ScriptEventSourceHolder::GetSingleton();
		if (!holder)
		{
			logger::warn("ScriptEventSourceHolder unavailable; the Dragonstone will not respond to activation");
			return;
		}
		holder->AddEventSink<RE::TESActivateEvent>(ActivateSink::GetSingleton());
		g_sinkRegistered = true;
		logger::info("Dragonstone activator resolved from {} at 0x{:08X} (\"{}\"); its High Hrothgar reference is 0x{:08X}; activate sink registered",
					 kPluginFileName, g_acti->GetFormID(), g_acti->GetName(), (g_acti->GetFormID() & 0xFFFFF000u) | kRefLocalFormID);
	}

	void OpenExchangeMenu()
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player) { return; }
		if (g_menuOpen.load(std::memory_order_acquire)) { return; }

		const float souls = player->AsActorValueOwner()->GetActorValue(RE::ActorValue::kDragonSouls);
		const int points = static_cast<int>(player->GetGameStatsData().perkCount);
		const std::uint32_t rate = std::max(1u, settings::general::soulsPerPoint);

		const std::string title = std::format(
			"The Dragonstone hums with the souls of the slain.\n\nDragon souls: {:.0f}    Perk points: {}\nEach perk point costs {} dragon soul{}.",
			souls, points, rate, rate == 1 ? "" : "s");

		RE::BSTArray<RE::BSString> options;
		for (const std::uint32_t n : kPointsPerButton)
		{
			options.push_back(RE::BSString(std::format("{} perk point{} ({} soul{})", n, n == 1 ? "" : "s", n * rate, n * rate == 1 ? "" : "s").c_str()));
		}
		options.push_back(RE::BSString("Leave"));

		RE::BSTSmartPointer<RE::IMessageBoxCallback> callback = RE::make_smart<ExchangeCallback>();
		g_menuOpen.store(true, std::memory_order_release);
		g_activations.fetch_add(1, std::memory_order_relaxed);
		RE::UI__OpenMessageBox(RE::BSString(title.c_str()), callback, 0, 25, 4, options);
		logger::debug("exchange menu opened (souls {:.0f}, points {}, rate {})", souls, points, rate);
	}

	void Pick(std::uint32_t a_index)
	{
		// One choice per opening: the first pick (button callback or DevBench) consumes the
		// open state; anything after it - like the box closing later - is ignored.
		if (!g_menuOpen.exchange(false, std::memory_order_acq_rel))
		{
			logger::debug("exchange menu: choice {} ignored - no menu is open", a_index);
			return;
		}
		if (a_index >= std::size(kPointsPerButton))
		{
			logger::debug("exchange menu: left without exchanging");
			return;
		}
		const std::uint32_t wanted = kPointsPerButton[a_index];
		const int granted = SoulsToPerks::Convert(static_cast<int>(wanted));
		std::string note;
		if (granted <= 0) { note = "Not enough dragon souls."; }
		else if (static_cast<std::uint32_t>(granted) < wanted) { note = std::format("{} of {} perk points granted - not enough souls for the rest.", granted, wanted); }
		else { note = std::format("{} perk point{} granted.", granted, granted == 1 ? "" : "s"); }
#if RUNTIME_LINE == 17
		RE::SendHUDMessage::ShowHUDMessage(note.c_str(), nullptr, true);
#else
		RE::DebugNotification(note.c_str());
#endif
		logger::info("exchange menu: button {} ({} points) -> {}", a_index, wanted, note);
	}

	State GetState()
	{
		State s;
		s.resolved = g_acti != nullptr && g_sinkRegistered;
		s.refFormID = g_acti ? ((g_acti->GetFormID() & 0xFFFFF000u) | kRefLocalFormID) : 0;
		s.menuOpen = g_menuOpen.load(std::memory_order_acquire);
		s.activations = g_activations.load(std::memory_order_relaxed);
		return s;
	}
}
