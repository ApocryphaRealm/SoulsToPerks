#include "PCH.h"

#include "UI.h"

#include "SKSEMenuFramework.h"

#include "Dragonstone.h"
#include "Settings.h"
#include "SoulsToPerks.h"

#include "utils/Logger.h"
#include "utils/Strings.h"
#include "utils/Toggle.h"

#include <algorithm>
#include <functional>
#include <string>
#include <vector>

namespace UI
{
	namespace
	{
		std::string statusMessage;
		std::string selectedSlider;

		constexpr const char* kLogLevelNames[] = { "Trace", "Debug", "Info", "Warning", "Error", "Critical", "Off" };
		constexpr const char* kLogLevelKeys[] = { "STP_LogLevel_Trace", "STP_LogLevel_Debug", "STP_LogLevel_Info",
													"STP_LogLevel_Warning", "STP_LogLevel_Error", "STP_LogLevel_Critical", "STP_LogLevel_Off" };
		constexpr int kLogLevelCount = 7;

		void OnMainThread(std::function<void()> a_task)
		{
			if (auto* taskInterface = SKSE::GetTaskInterface())
			{
				taskInterface->AddTask(std::move(a_task));
			}
		}

		bool HasRequiredExports()
		{
			constexpr const char* required[] = {
				"AddSectionItem",
				"igTextV",
				"igTextDisabledV",
				"igTextWrappedV",
				"igSetTooltipV",
				"igSeparatorText",
				"igCombo_Str_arr",
				"igSliderFloat",
				"igIsKeyPressed_Bool",
				"igIsItemClicked",
				"igIsItemActive",
				"igIsItemHovered",
				"igButton",
				"igSameLine",
				"igSpacing",
				"igPushItemWidth",
				"igPopItemWidth",
				"igGetCursorScreenPos",
				"igGetWindowDrawList",
				"igGetFrameHeight",
				"igInvisibleButton",
				"igPushID_Str",
				"igPopID",
				"ImDrawList_AddRectFilled",
				"ImDrawList_AddCircleFilled"
			};

			for (const char* name : required)
			{
				if (!GetMenuFrameworkFunction<void*>(name))
				{
					logger::warn("The menu framework does not export \"{}\"", name);
					return false;
				}
			}
			return true;
		}

		void HelpMarker(const char* a_description)
		{
			ImGuiMCP::SameLine();
			ImGuiMCP::TextDisabled("%s", strings::TR("STP_HelpMark", "(?)"));
			if (ImGuiMCP::IsItemHovered())
			{
				ImGuiMCP::SetTooltip("%s", a_description);
			}
		}

		bool NudgeableSlider(const char* a_label, float* a_value, float a_min, float a_max,
							 const char* a_format, float a_step)
		{
			bool changed = ImGuiMCP::SliderFloat(a_label, a_value, a_min, a_max, a_format);
			if (ImGuiMCP::IsItemClicked() || ImGuiMCP::IsItemActive()) { selectedSlider = a_label; }
			if (selectedSlider == a_label)
			{
				float nudge = 0.0F;
				if (ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_LeftArrow) || ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_DownArrow)) { nudge -= a_step; }
				if (ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_RightArrow) || ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_UpArrow)) { nudge += a_step; }
				if (nudge != 0.0F)
				{
					*a_value = std::clamp(*a_value + nudge, a_min, a_max);
					changed = true;
				}
				ImGuiMCP::SameLine();
				ImGuiMCP::TextDisabled("<-->");
			}
			return changed;
		}

		void RenderGeneralSection()
		{
			using namespace settings;

			ImGuiMCP::SeparatorText(strings::TR("STP_Title", "Souls to perks"));

			const auto s = SoulsToPerks::GetState();
			ImGuiMCP::Text(strings::TR("STP_SoulsPerksStatus", "Dragon souls: %.0f    Perk points: %d"), s.dragonSouls, static_cast<int>(s.perkPoints));

			float rate = static_cast<float>(general::soulsPerPoint);
			if (NudgeableSlider(strings::TR("STP_SoulsPerPoint", "Souls per point"), &rate, 1.0F, 10.0F, "%.0f", 1.0F))
			{
				general::soulsPerPoint = static_cast<std::uint32_t>(rate + 0.5F);
			}
			HelpMarker(strings::TR("STP_HelpSoulsPerPoint", "How many dragon souls one perk point costs."));

			if (ImGuiMCP::Button(strings::TR("STP_ConvertBtn", "Convert one point")))
			{
				SoulsToPerks::RequestConvertOne();
				statusMessage = strings::TR("STP_StatusConverting", "Converting...");
			}
			HelpMarker(strings::TR("STP_HelpConvert", "Spends the souls and grants one perk point, if you have enough."));

			ImGuiMCP::Toggle(strings::TR("STP_AutoConvert", "Convert automatically"), &general::autoConvert);
			HelpMarker(strings::TR("STP_HelpAutoConvert", "Whenever you have enough souls, they convert on their own. Off by default - spending souls is your call."));

			const auto d = Dragonstone::GetState();
			if (d.resolved)
			{
				ImGuiMCP::TextWrapped("%s", strings::TR("STP_DragonstoneResolved", "The Dragonstone stands in the High Hrothgar courtyard - activate it to exchange souls in the world."));
			}
			else
			{
				ImGuiMCP::TextWrapped("%s", strings::TR("STP_EslNotLoaded", "SoulsToPerks.esl is not loaded - the Dragonstone at High Hrothgar cannot exist. Enable it in your mod manager."));
			}
		}

		void RenderDebugSection()
		{
			using namespace settings;

			ImGuiMCP::SeparatorText(strings::TR("STP_Debug", "Debug"));

			int level = static_cast<int>(debug::logLevel);
			level = std::clamp(level, 0, kLogLevelCount - 1);
			// Rebuilt from TR'd entries every frame (plan 2.2); labelStore owns the translated
			// bytes for this call so the const char* pointers handed to Combo stay valid.
			std::vector<std::string> logLevelLabelStore;
			logLevelLabelStore.reserve(kLogLevelCount);
			for (int i = 0; i < kLogLevelCount; ++i)
			{
				logLevelLabelStore.push_back(strings::TR(kLogLevelKeys[i], kLogLevelNames[i]));
			}
			std::vector<const char*> logLevelLabels;
			logLevelLabels.reserve(logLevelLabelStore.size());
			for (const auto& s : logLevelLabelStore) { logLevelLabels.push_back(s.c_str()); }
			if (ImGuiMCP::Combo(strings::TR("STP_LogLevel", "Log level"), &level, logLevelLabels.data(), kLogLevelCount))
			{
				debug::logLevel = static_cast<std::uint32_t>(level);
				ApplyLogLevel();
			}
			HelpMarker(strings::TR("STP_HelpLogLevel", "Applies immediately. The log is at Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log."));
		}

		void RenderButtons()
		{
			ImGuiMCP::SeparatorText("");

			if (ImGuiMCP::Button(strings::TR("STP_SaveBtn", "Save")))
			{
				statusMessage = strings::TR("STP_StatusSaving", "Saving...");
				OnMainThread([]() {
					statusMessage = settings::Save() ? strings::TR("STP_StatusSaved", "Settings saved.")
													   : strings::TR("STP_StatusSaveFail", "Could not write the INI. See the log for why.");
				});
			}
			HelpMarker(strings::TR("STP_HelpSave", "Writes every setting on this page to the plugin's INI so it survives a restart."));

			ImGuiMCP::SameLine();

			if (ImGuiMCP::Button(strings::TR("STP_ReloadBtn", "Reload from INI")))
			{
				statusMessage = strings::TR("STP_StatusReloading", "Reloading...");
				OnMainThread([]() {
					statusMessage = settings::Reload() ? strings::TR("STP_StatusReloaded", "Settings reloaded from the INI.")
													   : strings::TR("STP_StatusReloadFail", "Could not read the INI. See the log for why.");
				});
			}
			HelpMarker(strings::TR("STP_HelpReload", "Throws away any change made here since the last save and re-reads the INI from disk."));

			ImGuiMCP::SameLine();

			if (ImGuiMCP::Button(strings::TR("STP_RestoreBtn", "Restore defaults")))
			{
				OnMainThread([]() {
					settings::RestoreDefaults();
					logger::debug("Restored default settings");
				});
				statusMessage = strings::TR("STP_StatusRestored", "Defaults restored. Press Save to keep them.");
			}
			HelpMarker(strings::TR("STP_HelpRestore", "Puts every setting back to its fresh-install value. Nothing is written until you press Save."));

			if (!statusMessage.empty())
			{
				ImGuiMCP::TextWrapped("%s", statusMessage.c_str());
			}

			ImGuiMCP::Spacing();
			ImGuiMCP::Text("%s", settings::GetIniPath().c_str());
		}
	}

	void Register()
	{
		if (!SKSEMenuFramework::IsInstalled())
		{
			logger::info("No menu framework is installed; settings will be read from the INI only");
			return;
		}
		if (!HasRequiredExports())
		{
			logger::warn("The installed menu framework is older than this plugin's settings "
						 "menu needs. Update it (Apocrypha Menu Framework, or SKSE Menu "
						 "Framework version 3 or newer).");
			return;
		}

		SKSEMenuFramework::SetSection("Souls to Perks");
		SKSEMenuFramework::AddSectionItem("Settings", SettingsPanel::Render);
		logger::info("Registered the settings page with the menu framework");
	}

	void __stdcall SettingsPanel::Render()
	{
		strings::Tick();

		ImGuiMCP::TextWrapped("%s", strings::TR("STP_Intro", "Changes apply as soon as you make them. Press Save to keep them for the next time you play."));
		ImGuiMCP::Spacing();

		ImGuiMCP::PushItemWidth(260.0F);

		RenderGeneralSection();
		ImGuiMCP::Spacing();

		RenderDebugSection();
		ImGuiMCP::Spacing();

		ImGuiMCP::PopItemWidth();

		RenderButtons();
	}
}
