// Souls to Perks - own code, GPL-3.0-or-later (2026-09-01). Dragon souls and perk points are both
// game-saved values (an actor value and the perkCount byte), so a conversion is a plain
// main-thread transfer - no hooks, no serialization. The Dragonstone (a placed activator in
// the tiny SoulsToPerks.esp) is the in-world way in; the settings page is the other.
#include "PCH.h"

#include "DevBenchTool.h"
#include "Dragonstone.h"
#include "Settings.h"
#include "SoulsToPerks.h"
#include "UI.h"

#include "utils/AddressLibraryGuard.h"
#include "utils/Logger.h"
#include "utils/Strings.h"

namespace
{
	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type)
		{
		case SKSE::MessagingInterface::kPostLoad:
			DevBenchTool::Init(false);
			break;
		case SKSE::MessagingInterface::kDataLoaded:
			strings::Configure("SoulsToPerks");
			UI::Register();
			SoulsToPerks::Install();
			Dragonstone::Install();
			DevBenchTool::Init(true);
			break;
		default:
			break;
		}
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SKSE::log::init("SoulsToPerks");
	// Address Library pre-check (the guard every mod of ours carries), BEFORE SKSE::Init, which opens the
	// Address Library itself (logic library 6026): a missing file gets a message naming it and the plugin
	// loads inert instead of CommonLibSSE-NG's bare failure line.
	if (!AddressLibraryGuard::Guard("Souls to Perks"))
	{
		return true;
	}
	SKSE::Init(a_skse);

	settings::Init("SoulsToPerks.ini");
	settings::ApplyLogLevel();

	logger::info("Souls to Perks {} loading",
				 SKSE::PluginDeclaration::GetSingleton()->GetVersion().string("."));

	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);

	return true;
}
