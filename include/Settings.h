#pragma once

// Souls to Perks - settings. Plain-file INI (redirector-proof, the project standard).

#include <cstdint>
#include <string>

namespace settings
{
	namespace debug
	{
		inline std::uint32_t logLevel = 0;  // uLogLevel:Debug
	}

	namespace general
	{
		inline std::uint32_t soulsPerPoint = 1;  // uSoulsPerPoint:General - dragon souls per perk point
		inline bool autoConvert = false;         // bAutoConvert:General - convert on its own when souls suffice
	}

	void Init(const std::string& a_iniFileName);
	bool Reload();
	bool Save();
	void RestoreDefaults();
	void ApplyLogLevel();
	const std::string& GetIniPath();
}
