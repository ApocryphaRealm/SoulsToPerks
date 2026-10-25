#include "PCH.h"

#include "Dragonstone.h"

#include "Settings.h"
#include "SoulsToPerks.h"
#include "utils/Logger.h"

#include <algorithm>
#include <atomic>
#include <format>
#include <string>
#include <vector>

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
		static REL::Relocation<func_t> func{ REL::RelocationID(51421, REL::Module::get().version() < SKSE::RUNTIME_SSE_1_6_1130 ? 52270 : 442726) };
		return func(a_title, a_callback, a_arg3, a_arg4, a_arg5, a_options);
	}

	// The engine's own reference SetScale (what Papyrus ObjectReference.SetScale ends in): stores the
	// scale and rescales loaded 3D. CommonLibSSE-NG 7.2 declares it as TESObjectREFR::SetScale with
	// these IDs; 3.7 (the SE/AE line) does not, so both lines call it through this one wrapper.
	void TESObjectREFR__SetScale(TESObjectREFR* a_ref, float a_scale)
	{
		using func_t = decltype(&TESObjectREFR__SetScale);
		static REL::Relocation<func_t> func{ REL::RelocationID(19239, 19665) };
		func(a_ref, a_scale);
	}
}

namespace Dragonstone
{
	namespace
	{
		// The contract with SoulsToPerks.esp (tools/Build-SoulsToPerksEsl.py): ONE record,
		// 0x800 ACTI (the Dragonstone). Since 1.0.7 the plugin places nothing and overrides no
		// vanilla record - no CELL, no WRLD, no REFR (the owner, 2026-10-25). The stone is put
		// into the High Hrothgar courtyard here, at runtime, when that cell finishes loading.
		// Activation matches the BASE object, so any Dragonstone made from this activator works.
		constexpr const char* kPluginFileName = "SoulsToPerks.esp";
		constexpr RE::FormID kActivatorLocalFormID = 0x800;
		constexpr std::uint32_t kPointsPerButton[] = { 1, 5, 10 };

		// Where the stone stands: Tamriel cell HighHrothgarExterior01 (Skyrim.esm 0x000096CC,
		// grid 13,-9), between the doors (x 52640) and the meditation spot (55054,-36007,23461),
		// south of the door axis so the path stays clear, facing the doors - the spot 1.0.6
		// placed it at through the plugin, read from Skyrim.esm's own courtyard markers.
		constexpr RE::FormID kCourtyardCellID = 0x000096CC;
		constexpr float kPosX = 54700.0F;
		constexpr float kPosY = -36600.0F;
		constexpr float kPosZ = 23461.0F;
		constexpr float kRotZ = 1.5708F;
		constexpr float kScale = 0.7F;

		RE::TESBoundObject* g_acti = nullptr;
		bool g_sinkRegistered = false;
		std::atomic<bool> g_menuOpen{ false };
		std::atomic<std::uint64_t> g_activations{ 0 };
		std::atomic<std::uint32_t> g_refFormID{ 0 };      // the courtyard stone, once seen this session
		std::atomic<std::uint32_t> g_courtyardCount{ 0 }; // stones in the courtyard after the last check
		std::atomic<std::uint32_t> g_placements{ 0 };     // stones created this session
		std::atomic<std::uint32_t> g_removed{ 0 };        // duplicates removed this session
		std::atomic<bool> g_ensureQueued{ false };

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

		// Makes sure exactly one Dragonstone stands in the courtyard. Main thread only.
		// The stone is an ordinary created reference: the game keeps it in the save like any
		// object placed at runtime, so on later visits and after a reload it is found here and
		// nothing new is made. If the game ever drops it, the next visit places it again; if two
		// are ever found, the extras are disabled and deleted. Removing the mod removes the
		// activator record the reference is built from.
		void EnsureCourtyardStone()
		{
			g_ensureQueued.store(false, std::memory_order_release);
			if (!g_acti) { return; }
			auto* form = RE::TESForm::LookupByID(kCourtyardCellID);
			auto* cell = form ? form->As<RE::TESObjectCELL>() : nullptr;
			if (!cell || !cell->IsAttached())
			{
				logger::debug("courtyard check skipped: cell 0x{:08X} {}", kCourtyardCellID, cell ? "is not attached" : "not found");
				return;
			}

			RE::TESObjectREFR* keep = nullptr;
			std::vector<RE::TESObjectREFR*> extras;
			cell->ForEachReference([&](RE::TESObjectREFR* a_ref) {
				if (a_ref && a_ref->GetBaseObject() == g_acti && !a_ref->IsDeleted())
				{
					if (!keep) { keep = a_ref; }
					else { extras.push_back(a_ref); }
				}
				return RE::BSContainer::ForEachResult::kContinue;
			});
			for (auto* extra : extras)
			{
				logger::warn("courtyard: removing duplicate Dragonstone 0x{:08X} (keeping 0x{:08X})", extra->GetFormID(), keep->GetFormID());
				extra->Disable();
				extra->SetDelete(true);
				g_removed.fetch_add(1, std::memory_order_relaxed);
			}

			if (!keep)
			{
				auto* dataHandler = RE::TESDataHandler::GetSingleton();
				auto* worldspace = cell->GetRuntimeData().worldSpace;
				if (!dataHandler || !worldspace)
				{
					logger::warn("courtyard: cannot place the Dragonstone (data handler {}, worldspace {})",
								 dataHandler ? "ok" : "missing", worldspace ? "ok" : "missing");
					return;
				}
				const auto handle = dataHandler->CreateReferenceAtLocation(
					g_acti, RE::NiPoint3{ kPosX, kPosY, kPosZ }, RE::NiPoint3{ 0.0F, 0.0F, kRotZ },
					cell, worldspace, nullptr, nullptr, RE::ObjectRefHandle{}, false, true);
				const auto placed = handle.get();
				if (!placed)
				{
					logger::error("courtyard: CreateReferenceAtLocation returned no reference - the Dragonstone is not placed");
					return;
				}
				RE::TESObjectREFR__SetScale(placed.get(), kScale);
				keep = placed.get();
				g_placements.fetch_add(1, std::memory_order_relaxed);
				logger::info("courtyard: Dragonstone placed as 0x{:08X} at ({:.0f}, {:.0f}, {:.0f})", keep->GetFormID(), kPosX, kPosY, kPosZ);
			}
			else
			{
				logger::info("courtyard: Dragonstone already stands as 0x{:08X}; nothing placed", keep->GetFormID());
			}
			g_refFormID.store(keep->GetFormID(), std::memory_order_release);
			g_courtyardCount.store(1, std::memory_order_release);
		}

		void QueueCourtyardCheck()
		{
			if (g_ensureQueued.exchange(true, std::memory_order_acq_rel)) { return; }
			if (auto* tasks = SKSE::GetTaskInterface()) { tasks->AddTask([]() { EnsureCourtyardStone(); }); }
			else { g_ensureQueued.store(false, std::memory_order_release); }
		}

		class CellLoadedSink : public RE::BSTEventSink<RE::TESCellFullyLoadedEvent>
		{
		public:
			static CellLoadedSink* GetSingleton()
			{
				static CellLoadedSink singleton;
				return &singleton;
			}

			RE::BSEventNotifyControl ProcessEvent(const RE::TESCellFullyLoadedEvent* a_event, RE::BSTEventSource<RE::TESCellFullyLoadedEvent>*) override
			{
				if (a_event && a_event->cell && a_event->cell->GetFormID() == kCourtyardCellID)
				{
					logger::debug("courtyard cell fully loaded; checking for the Dragonstone");
					QueueCourtyardCheck();
				}
				return RE::BSEventNotifyControl::kContinue;
			}
		};
	}

	void OnGameLoaded()
	{
		// A save made in or near the courtyard has the cell loaded as the game comes up; check once
		// after every load and new game too (a no-op unless the courtyard is attached).
		QueueCourtyardCheck();
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
		holder->AddEventSink<RE::TESCellFullyLoadedEvent>(CellLoadedSink::GetSingleton());
		g_sinkRegistered = true;
		logger::info("Dragonstone activator resolved from {} at 0x{:08X} (\"{}\"); activate and cell-load sinks registered - "
					 "the stone is placed in the High Hrothgar courtyard (cell 0x{:08X}) when that cell loads",
					 kPluginFileName, g_acti->GetFormID(), g_acti->GetName(), kCourtyardCellID);
	}

	void OpenExchangeMenu()
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player || !player->GetParentCell()) { return; }
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
		s.refFormID = g_refFormID.load(std::memory_order_acquire);
		s.courtyardCount = g_courtyardCount.load(std::memory_order_acquire);
		s.placements = g_placements.load(std::memory_order_relaxed);
		s.duplicatesRemoved = g_removed.load(std::memory_order_relaxed);
		s.menuOpen = g_menuOpen.load(std::memory_order_acquire);
		s.activations = g_activations.load(std::memory_order_relaxed);
		return s;
	}
}
