# -*- coding: utf-8 -*-
"""gen-translations.py - builds the eleven SoulsToPerks_<language>.txt files.

The English key list is extracted from the PATCHED source/UI.cpp by regex on
strings::TR("KEY", "text") so it can never drift from the code. The other ten languages are
this project's own translations of that list, held below as parallel dictionaries.

Writes REPO/dist/Interface/Translations/SoulsToPerks_<language>.txt for english + the owner's
ten languages (UTF-16LE with a BOM, one "$key<TAB>text" per line, literal "\\n" for an embedded
line break, CRLF records - the SKSE/SkyUI shape AMF's own Strings.cpp reads).

Run: `python tools/gen-translations.py` from the repo root or anywhere (paths are relative to
this script's grandparent directory).
"""
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["english", "japanese", "korean", "chinese", "russian", "german", "french", "spanish", "italian", "polish", "czech"]

TR_RE = re.compile(r'strings::TR\(\s*"((?:[^"\\]|\\.)+)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)')


def unescape(s):
    return s.encode("latin-1", "backslashreplace").decode("unicode_escape") if "\\" in s else s


KEY_ARRAY_RE = re.compile(r'constexpr const char\* kLogLevelKeys\[\]\s*=\s*\{([^}]*)\};', re.S)
NAME_ARRAY_RE = re.compile(r'constexpr const char\* kLogLevelNames\[\]\s*=\s*\{([^}]*)\};', re.S)
STR_LIT_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def read_keys():
    path = os.path.join(REPO, "source", "UI.cpp")
    src = io.open(path, "r", encoding="utf-8").read()
    keys = {}
    order = []
    for m in TR_RE.finditer(src):
        key, text = unescape(m.group(1)), unescape(m.group(2))
        if key in keys and keys[key] != text:
            raise RuntimeError(f"duplicate key {key!r} with two different English texts: {keys[key]!r} vs {text!r}")
        if key not in keys:
            order.append(key)
        keys[key] = text

    # The log-level Combo's option labels are looked up by a parallel key array
    # (kLogLevelKeys[i] -> kLogLevelNames[i]) rather than a literal strings::TR(...) call, since
    # the option text is rebuilt into a std::vector per frame. Pair the two arrays positionally.
    km = KEY_ARRAY_RE.search(src)
    nm = NAME_ARRAY_RE.search(src)
    if not km or not nm:
        raise RuntimeError("could not find kLogLevelKeys/kLogLevelNames arrays in source/UI.cpp")
    array_keys = [unescape(s) for s in STR_LIT_RE.findall(km.group(1))]
    array_names = [unescape(s) for s in STR_LIT_RE.findall(nm.group(1))]
    if len(array_keys) != len(array_names):
        raise RuntimeError(f"kLogLevelKeys ({len(array_keys)}) and kLogLevelNames ({len(array_names)}) length mismatch")
    for key, text in zip(array_keys, array_names):
        if key in keys and keys[key] != text:
            raise RuntimeError(f"duplicate key {key!r} with two different English texts: {keys[key]!r} vs {text!r}")
        if key not in keys:
            order.append(key)
        keys[key] = text

    return keys, order


# ------------------------------------------------------------------------------------------------
# Translations for every key found in source/UI.cpp. Plain, literal renderings of the UI text;
# every printf specifier is kept exactly; product names (Skyrim, Apocrypha Menu Framework, Souls
# to Perks) stay untranslated; file names (SoulsToPerks.log, SoulsToPerks.esl, the INI) stay
# untranslated inside the translated sentence; Skyrim's own terms (Dragon Soul, perk, perk point)
# use each language's in-game vocabulary.
# ------------------------------------------------------------------------------------------------
TRANSLATIONS = {
    "STP_HelpMark": {
        "japanese": "(?)", "korean": "(?)", "chinese": "(?)", "russian": "(?)", "german": "(?)",
        "french": "(?)", "spanish": "(?)", "italian": "(?)", "polish": "(?)", "czech": "(?)",
    },
    "STP_Title": {
        "japanese": "魂からパーク", "korean": "영혼을 펄크로", "chinese": "灵魂化异能",
        "russian": "Души в перки", "german": "Seelen zu Perks", "french": "Âmes en capacités",
        "spanish": "Almas a dotes", "italian": "Anime in abilità speciali", "polish": "Dusze na atuty",
        "czech": "Duše na schopnosti",
    },
    "STP_SoulsPerksStatus": {
        "japanese": "ドラゴンソウル: %.0f    パークポイント: %d", "korean": "드래곤 소울: %.0f    펄크 포인트: %d",
        "chinese": "龙魂: %.0f    异能点: %d", "russian": "Драконьи души: %.0f    Очки перков: %d",
        "german": "Drachenseelen: %.0f    Perkpunkte: %d", "french": "Âmes de dragon : %.0f    Points de capacité : %d",
        "spanish": "Almas de dragón: %.0f    Puntos de dote: %d", "italian": "Anime di draghi: %.0f    Punti abilità: %d",
        "polish": "Dusze draka: %.0f    Punkty atutów: %d", "czech": "Dračí duše: %.0f    Body schopností: %d",
    },
    "STP_SoulsPerPoint": {
        "japanese": "1ポイントあたりのソウル数", "korean": "포인트당 소울", "chinese": "每点所需灵魂",
        "russian": "Душ на очко", "german": "Seelen pro Punkt", "french": "Âmes par point",
        "spanish": "Almas por punto", "italian": "Anime per punto", "polish": "Dusze na punkt",
        "czech": "Duše na bod",
    },
    "STP_HelpSoulsPerPoint": {
        "japanese": "1つのパークポイントに必要なドラゴンソウルの数。",
        "korean": "펄크 포인트 하나에 필요한 드래곤 소울의 수입니다.",
        "chinese": "一点异能点需要消耗多少龙魂。",
        "russian": "Сколько драконьих душ стоит одно очко перка.",
        "german": "Wie viele Drachenseelen ein Perkpunkt kostet.",
        "french": "Combien d'âmes de dragon coûte un point de capacité.",
        "spanish": "Cuántas almas de dragón cuesta un punto de dote.",
        "italian": "Quante anime di draghi costa un punto abilità.",
        "polish": "Ile dusz draka kosztuje jeden punkt atutu.",
        "czech": "Kolik dračích duší stojí jeden bod schopnosti.",
    },
    "STP_ConvertBtn": {
        "japanese": "1ポイント変換", "korean": "1포인트 변환", "chinese": "转换一点",
        "russian": "Обменять одно очко", "german": "Einen Punkt umwandeln", "french": "Convertir un point",
        "spanish": "Convertir un punto", "italian": "Converti un punto", "polish": "Zamień jeden punkt",
        "czech": "Převést jeden bod",
    },
    "STP_StatusConverting": {
        "japanese": "変換中...", "korean": "변환 중...", "chinese": "正在转换...", "russian": "Обмен...",
        "german": "Wird umgewandelt...", "french": "Conversion...", "spanish": "Convirtiendo...",
        "italian": "Conversione...", "polish": "Zamienianie...", "czech": "Převádí se...",
    },
    "STP_HelpConvert": {
        "japanese": "ソウルを消費し、十分にあれば1パークポイントを与えます。",
        "korean": "소울을 소비하고, 충분하면 펄크 포인트 하나를 지급합니다.",
        "chinese": "消耗灵魂,若数量足够则获得一点异能点。",
        "russian": "Тратит души и, если их достаточно, даёт одно очко перка.",
        "german": "Verbraucht die Seelen und gewährt einen Perkpunkt, sofern genug vorhanden sind.",
        "french": "Dépense les âmes et accorde un point de capacité, si vous en avez assez.",
        "spanish": "Gasta las almas y otorga un punto de dote, si tienes suficientes.",
        "italian": "Consuma le anime e concede un punto abilità, se ne hai a sufficienza.",
        "polish": "Wydaje dusze i przyznaje jeden punkt atutu, jeśli masz ich wystarczająco.",
        "czech": "Spotřebuje duše a udělí jeden bod schopnosti, pokud jich máte dost.",
    },
    "STP_AutoConvert": {
        "japanese": "自動変換", "korean": "자동 변환", "chinese": "自动转换", "russian": "Автообмен",
        "german": "Automatisch umwandeln", "french": "Convertir automatiquement", "spanish": "Convertir automáticamente",
        "italian": "Converti automaticamente", "polish": "Zamieniaj automatycznie", "czech": "Automaticky převádět",
    },
    "STP_HelpAutoConvert": {
        "japanese": "十分なソウルがあれば自動的に変換されます。既定はオフ - ソウルを使うかどうかはあなたの判断です。",
        "korean": "소울이 충분하면 스스로 변환됩니다. 기본값은 꺼짐 - 소울을 쓸지는 당신의 선택입니다.",
        "chinese": "灵魂足够时会自动转换。默认关闭 - 是否花费灵魂由你决定。",
        "russian": "Как только душ достаточно, они обмениваются сами. По умолчанию выключено - тратить души или нет, решаете вы.",
        "german": "Sobald genug Seelen vorhanden sind, werden sie von selbst umgewandelt. Standardmäßig aus - das Ausgeben der Seelen bleibt deine Entscheidung.",
        "french": "Dès que vous avez assez d'âmes, elles se convertissent seules. Désactivé par défaut - dépenser les âmes reste votre choix.",
        "spanish": "En cuanto tengas suficientes almas, se convierten solas. Desactivado por defecto - gastar almas es decisión tuya.",
        "italian": "Non appena hai anime sufficienti, si convertono da sole. Disattivato per impostazione predefinita - spendere le anime resta una tua scelta.",
        "polish": "Gdy masz wystarczająco dusz, zamieniają się sami. Domyślnie wyłączone - wydawanie dusz to twoja decyzja.",
        "czech": "Jakmile máte dost duší, samy se převedou. Výchozí stav: vypnuto - utrácení duší je vaše rozhodnutí.",
    },
    "STP_DragonstoneResolved": {
        "japanese": "ドラゴンストーンはハイ・フロスガーの中庭に立っています - 起動すると世界内でソウルを交換できます。",
        "korean": "드래곤스톤은 하이 흐로스가르 안뜰에 서 있습니다 - 상호작용하면 세계에서 소울을 교환할 수 있습니다.",
        "chinese": "龙石立于高吼修道院庭院之中 - 激活它即可在游戏世界中交换灵魂。",
        "russian": "Драконий камень стоит во дворе Высокого Хротгара - взаимодействуйте с ним, чтобы обменять души прямо в игровом мире.",
        "german": "Der Drachenstein steht im Hof von Hoher Hrothgar - aktiviere ihn, um Seelen direkt in der Welt umzutauschen.",
        "french": "La Pierre draconique se trouve dans la cour du Haut-Hrothgar - activez-la pour échanger des âmes dans le monde.",
        "spanish": "La Piedra dracónica se encuentra en el patio de Alto Hrothgar - actívala para intercambiar almas en el mundo.",
        "italian": "La Pietra di Draco si trova nel cortile dell'Alto Hrothgar - attivala per scambiare anime nel mondo.",
        "polish": "Kamień draka stoi na dworze Wysokiego Hrothgaru - aktywuj go, aby wymieniać dusze w świecie gry.",
        "czech": "Dračí kámen stojí na nádvoří Vysokého Hrothgaru - aktivujte jej pro směnu duší přímo ve světě.",
    },
    "STP_EslNotLoaded": {
        "japanese": "SoulsToPerks.esl が読み込まれていません - ハイ・フロスガーのドラゴンストーンは存在できません。Modマネージャーで有効にしてください。",
        "korean": "SoulsToPerks.esl 이(가) 로드되지 않았습니다 - 하이 흐로스가르의 드래곤스톤이 존재할 수 없습니다. 모드 매니저에서 활성화하세요.",
        "chinese": "SoulsToPerks.esl 未加载 - 高吼修道院的龙石无法存在。请在你的模组管理器中启用它。",
        "russian": "SoulsToPerks.esl не загружен - Драконий камень в Высоком Хротгаре не может существовать. Включите его в вашем менеджере модов.",
        "german": "SoulsToPerks.esl ist nicht geladen - der Drachenstein in Hoher Hrothgar kann nicht existieren. Aktiviere es in deinem Mod-Manager.",
        "french": "SoulsToPerks.esl n'est pas chargé - la Pierre draconique du Haut-Hrothgar ne peut pas exister. Activez-le dans votre gestionnaire de mods.",
        "spanish": "SoulsToPerks.esl no está cargado - la Piedra dracónica de Alto Hrothgar no puede existir. Actívalo en tu gestor de mods.",
        "italian": "SoulsToPerks.esl non è caricato - la Pietra di Draco dell'Alto Hrothgar non può esistere. Attivalo nel tuo gestore di mod.",
        "polish": "SoulsToPerks.esl nie jest wczytany - Kamień draka w Wysokim Hrothgarze nie może istnieć. Włącz go w swoim menedżerze modów.",
        "czech": "SoulsToPerks.esl není načten - Dračí kámen ve Vysokém Hrothgaru nemůže existovat. Povolte jej ve svém správci modů.",
    },
    "STP_Debug": {
        "japanese": "デバッグ", "korean": "디버그", "chinese": "调试", "russian": "Отладка", "german": "Debug",
        "french": "Débogage", "spanish": "Depuración", "italian": "Debug", "polish": "Debugowanie", "czech": "Ladění",
    },
    "STP_LogLevel": {
        "japanese": "ログレベル", "korean": "로그 레벨", "chinese": "日志级别", "russian": "Уровень журнала",
        "german": "Protokollstufe", "french": "Niveau de journal", "spanish": "Nivel de registro",
        "italian": "Livello di log", "polish": "Poziom logowania", "czech": "Úroveň logování",
    },
    "STP_LogLevel_Trace": {
        "japanese": "トレース", "korean": "추적", "chinese": "跟踪", "russian": "Трассировка", "german": "Trace",
        "french": "Trace", "spanish": "Trace", "italian": "Trace", "polish": "Trace", "czech": "Trace",
    },
    "STP_LogLevel_Debug": {
        "japanese": "デバッグ", "korean": "디버그", "chinese": "调试", "russian": "Отладка", "german": "Debug",
        "french": "Débogage", "spanish": "Depuración", "italian": "Debug", "polish": "Debugowanie", "czech": "Ladění",
    },
    "STP_LogLevel_Info": {
        "japanese": "情報", "korean": "정보", "chinese": "信息", "russian": "Информация", "german": "Info",
        "french": "Infos", "spanish": "Información", "italian": "Informazioni", "polish": "Informacje", "czech": "Informace",
    },
    "STP_LogLevel_Warning": {
        "japanese": "警告", "korean": "경고", "chinese": "警告", "russian": "Предупреждение", "german": "Warnung",
        "french": "Avertissement", "spanish": "Advertencia", "italian": "Avviso", "polish": "Ostrzeżenie", "czech": "Varování",
    },
    "STP_LogLevel_Error": {
        "japanese": "エラー", "korean": "오류", "chinese": "错误", "russian": "Ошибка", "german": "Fehler",
        "french": "Erreur", "spanish": "Error", "italian": "Errore", "polish": "Błąd", "czech": "Chyba",
    },
    "STP_LogLevel_Critical": {
        "japanese": "重大", "korean": "치명적", "chinese": "严重", "russian": "Критическая",
        "german": "Kritisch", "french": "Critique", "spanish": "Crítico", "italian": "Critico",
        "polish": "Krytyczny", "czech": "Kritická",
    },
    "STP_LogLevel_Off": {
        "japanese": "オフ", "korean": "끄기", "chinese": "关闭", "russian": "Отключено", "german": "Aus",
        "french": "Désactivé", "spanish": "Desactivado", "italian": "Disattivato", "polish": "Wyłączone", "czech": "Vypnuto",
    },
    "STP_HelpLogLevel": {
        "japanese": "即座に適用されます。ログは Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log にあります。",
        "korean": "즉시 적용됩니다. 로그는 Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log 에 있습니다.",
        "chinese": "立即生效。日志位于 Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log。",
        "russian": "Применяется немедленно. Журнал находится здесь: Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log.",
        "german": "Wird sofort angewendet. Das Log liegt unter Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log.",
        "french": "S'applique immédiatement. Le journal se trouve dans Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log.",
        "spanish": "Se aplica de inmediato. El registro está en Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log.",
        "italian": "Si applica immediatamente. Il log si trova in Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log.",
        "polish": "Stosowane natychmiast. Log znajduje się w Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log.",
        "czech": "Použije se okamžitě. Log je v Documents\\My Games\\Skyrim Special Edition\\SKSE\\SoulsToPerks.log.",
    },
    "STP_SaveBtn": {
        "japanese": "保存", "korean": "저장", "chinese": "保存", "russian": "Сохранить", "german": "Speichern",
        "french": "Enregistrer", "spanish": "Guardar", "italian": "Salva", "polish": "Zapisz", "czech": "Uložit",
    },
    "STP_StatusSaving": {
        "japanese": "保存中...", "korean": "저장 중...", "chinese": "正在保存...", "russian": "Сохранение...",
        "german": "Wird gespeichert...", "french": "Enregistrement...", "spanish": "Guardando...",
        "italian": "Salvataggio...", "polish": "Zapisywanie...", "czech": "Ukládání...",
    },
    "STP_StatusSaved": {
        "japanese": "設定を保存しました。", "korean": "설정을 저장했습니다.", "chinese": "设置已保存。",
        "russian": "Настройки сохранены.", "german": "Einstellungen gespeichert.", "french": "Paramètres enregistrés.",
        "spanish": "Ajustes guardados.", "italian": "Impostazioni salvate.", "polish": "Ustawienia zapisane.",
        "czech": "Nastavení uložena.",
    },
    "STP_StatusSaveFail": {
        "japanese": "INIの書き込みに失敗しました。理由はログを確認してください。",
        "korean": "INI를 쓸 수 없습니다. 이유는 로그를 확인하세요.",
        "chinese": "无法写入 INI。请查看日志了解原因。",
        "russian": "Не удалось записать INI. Причина — в журнале.",
        "german": "Die INI konnte nicht geschrieben werden. Der Grund steht im Log.",
        "french": "Impossible d'écrire l'INI. Voyez le journal pour la raison.",
        "spanish": "No se pudo escribir el INI. Consulta el registro para saber por qué.",
        "italian": "Impossibile scrivere l'INI. Consulta il log per il motivo.",
        "polish": "Nie można zapisać INI. Sprawdź log, aby dowiedzieć się dlaczego.",
        "czech": "Nelze zapsat INI. Důvod najdete v logu.",
    },
    "STP_HelpSave": {
        "japanese": "このページのすべての設定をプラグインのINIに書き込み、再起動後も残します。",
        "korean": "이 페이지의 모든 설정을 플러그인의 INI에 기록하여 재시작 후에도 유지되게 합니다.",
        "chinese": "将此页面的所有设置写入插件的 INI,使其在重启后仍然保留。",
        "russian": "Записывает каждую настройку этой страницы в INI плагина, чтобы она сохранилась после перезапуска.",
        "german": "Schreibt jede Einstellung dieser Seite in die INI des Plugins, damit sie einen Neustart überlebt.",
        "french": "Écrit chaque paramètre de cette page dans le fichier INI du plugin afin qu'il survive à un redémarrage.",
        "spanish": "Escribe cada ajuste de esta página en el INI del plugin para que sobreviva a un reinicio.",
        "italian": "Scrive ogni impostazione di questa pagina nell'INI del plugin, così sopravvive a un riavvio.",
        "polish": "Zapisuje każde ustawienie tej strony do pliku INI wtyczki, dzięki czemu przetrwa restart.",
        "czech": "Zapíše každé nastavení této stránky do INI pluginu, aby přežilo restart.",
    },
    "STP_ReloadBtn": {
        "japanese": "INIから再読み込み", "korean": "INI에서 다시 불러오기", "chinese": "从 INI 重新加载",
        "russian": "Перезагрузить из INI", "german": "Aus INI neu laden", "french": "Recharger depuis l'INI",
        "spanish": "Recargar desde el INI", "italian": "Ricarica dall'INI", "polish": "Wczytaj ponownie z INI",
        "czech": "Znovu načíst z INI",
    },
    "STP_StatusReloading": {
        "japanese": "再読み込み中...", "korean": "다시 불러오는 중...", "chinese": "正在重新加载...",
        "russian": "Перезагрузка...", "german": "Wird neu geladen...", "french": "Rechargement...",
        "spanish": "Recargando...", "italian": "Ricaricamento...", "polish": "Wczytywanie ponowne...",
        "czech": "Znovu se načítá...",
    },
    "STP_StatusReloaded": {
        "japanese": "INIから設定を再読み込みしました。", "korean": "INI에서 설정을 다시 불러왔습니다.",
        "chinese": "已从 INI 重新加载设置。", "russian": "Настройки перезагружены из INI.",
        "german": "Einstellungen aus der INI neu geladen.", "french": "Paramètres rechargés depuis l'INI.",
        "spanish": "Ajustes recargados desde el INI.", "italian": "Impostazioni ricaricate dall'INI.",
        "polish": "Ustawienia wczytane ponownie z INI.", "czech": "Nastavení znovu načtena z INI.",
    },
    "STP_StatusReloadFail": {
        "japanese": "INIの読み込みに失敗しました。理由はログを確認してください。",
        "korean": "INI를 읽을 수 없습니다. 이유는 로그를 확인하세요.",
        "chinese": "无法读取 INI。请查看日志了解原因。",
        "russian": "Не удалось прочитать INI. Причина — в журнале.",
        "german": "Die INI konnte nicht gelesen werden. Der Grund steht im Log.",
        "french": "Impossible de lire l'INI. Voyez le journal pour la raison.",
        "spanish": "No se pudo leer el INI. Consulta el registro para saber por qué.",
        "italian": "Impossibile leggere l'INI. Consulta il log per il motivo.",
        "polish": "Nie można odczytać INI. Sprawdź log, aby dowiedzieć się dlaczego.",
        "czech": "Nelze přečíst INI. Důvod najdete v logu.",
    },
    "STP_HelpReload": {
        "japanese": "最後の保存以降にここで行った変更をすべて捨て、INIをディスクから再読み込みします。",
        "korean": "마지막 저장 이후 여기서 만든 변경 사항을 모두 버리고 INI를 디스크에서 다시 읽습니다.",
        "chinese": "放弃自上次保存以来在此处所做的任何更改,并从磁盘重新读取 INI。",
        "russian": "Отбрасывает все изменения, сделанные здесь с последнего сохранения, и заново считывает INI с диска.",
        "german": "Verwirft jede hier seit dem letzten Speichern vorgenommene Änderung und liest die INI erneut von der Festplatte.",
        "french": "Annule tout changement effectué ici depuis le dernier enregistrement et relit l'INI depuis le disque.",
        "spanish": "Descarta cualquier cambio hecho aquí desde el último guardado y vuelve a leer el INI desde el disco.",
        "italian": "Scarta ogni modifica fatta qui dall'ultimo salvataggio e rilegge l'INI dal disco.",
        "polish": "Odrzuca wszelkie zmiany wprowadzone tutaj od ostatniego zapisu i ponownie odczytuje INI z dysku.",
        "czech": "Zahodí všechny změny provedené zde od posledního uložení a znovu načte INI z disku.",
    },
    "STP_RestoreBtn": {
        "japanese": "既定値に戻す", "korean": "기본값으로 복원", "chinese": "恢复默认值", "russian": "Восстановить умолч.",
        "german": "Standard wiederherstellen", "french": "Restaurer les valeurs par défaut",
        "spanish": "Restaurar valores predeterminados", "italian": "Ripristina i valori predefiniti",
        "polish": "Przywróć wartości domyślne", "czech": "Obnovit výchozí",
    },
    "STP_StatusRestored": {
        "japanese": "既定値に戻しました。保存を押して確定してください。",
        "korean": "기본값으로 복원했습니다. 유지하려면 저장을 누르세요.",
        "chinese": "已恢复默认值。按保存以保留它们。",
        "russian": "Значения по умолчанию восстановлены. Нажмите «Сохранить», чтобы закрепить их.",
        "german": "Standardwerte wiederherstellt. Drücke Speichern, um sie zu behalten.",
        "french": "Valeurs par défaut restaurées. Appuyez sur Enregistrer pour les conserver.",
        "spanish": "Valores predeterminados restaurados. Pulsa Guardar para conservarlos.",
        "italian": "Valori predefiniti ripristinati. Premi Salva per conservarli.",
        "polish": "Przywrócono wartości domyślne. Naciśnij Zapisz, aby je zachować.",
        "czech": "Výchozí hodnoty obnoveny. Stiskněte Uložit, abyste je zachovali.",
    },
    "STP_HelpRestore": {
        "japanese": "新規インストール時の値にすべての設定を戻します。保存ボタンを押すまで何も書き込まれません。",
        "korean": "새로 설치했을 때의 값으로 모든 설정을 되돌립니다. 저장을 누르기 전까지는 아무것도 기록되지 않습니다.",
        "chinese": "将每个设置恢复为全新安装时的值。在你按下保存之前,不会写入任何内容。",
        "russian": "Возвращает каждую настройку к значению, которое было бы при свежей установке. Ничего не записывается, пока вы не нажмёте «Сохранить».",
        "german": "Setzt jede Einstellung auf den Wert zurück, den sie bei einer frischen Installation hätte. Nichts wird geschrieben, bis du auf Speichern drückst.",
        "french": "Remet chaque paramètre à sa valeur d'une installation neuve. Rien n'est écrit avant que vous n'appuyiez sur Enregistrer.",
        "spanish": "Devuelve cada ajuste al valor que tendría en una instalación nueva. No se escribe nada hasta que pulses Guardar.",
        "italian": "Riporta ogni impostazione al valore che avrebbe in un'installazione nuova. Non viene scritto nulla finché non premi Salva.",
        "polish": "Przywraca każde ustawienie do wartości z nowej instalacji. Nic nie zostaje zapisane, dopóki nie naciśniesz Zapisz.",
        "czech": "Vrátí každé nastavení na hodnotu, jakou by mělo při čerstvé instalaci. Nic se nezapíše, dokud nestisknete Uložit.",
    },
    "STP_Intro": {
        "japanese": "変更はすぐに適用されます。次回プレイ時にも残すには保存を押してください。",
        "korean": "변경 사항은 즉시 적용됩니다. 다음에 플레이할 때도 유지하려면 저장을 누르세요.",
        "chinese": "更改会立即生效。按保存可在下次游玩时保留它们。",
        "russian": "Изменения применяются сразу же. Нажмите «Сохранить», чтобы они остались и в следующий раз.",
        "german": "Änderungen wirken sofort. Drücke Speichern, um sie für das nächste Mal zu behalten.",
        "french": "Les changements s'appliquent dès que vous les faites. Appuyez sur Enregistrer pour les garder la prochaine fois.",
        "spanish": "Los cambios se aplican en cuanto los haces. Pulsa Guardar para conservarlos la próxima vez que juegues.",
        "italian": "Le modifiche si applicano non appena le fai. Premi Salva per conservarle per la prossima partita.",
        "polish": "Zmiany obowiązują natychmiast po ich wprowadzeniu. Naciśnij Zapisz, aby zachować je na następną rozgrywkę.",
        "czech": "Změny se použijí okamžitě, jak je provedete. Stiskněte Uložit, abyste je zachovali pro příští hraní.",
    },
}


def write_translation_file(path, entries):
    lines = []
    for key, text in entries.items():
        escaped = text.replace("\r\n", "\n").replace("\n", "\\n")
        lines.append(f"${key}\t{escaped}")
    body = "\r\n".join(lines) + "\r\n"
    data = b"\xff\xfe" + body.encode("utf-16-le")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def main():
    keys, order = read_keys()
    missing_translation_keys = [k for k in order if k not in TRANSLATIONS]
    if missing_translation_keys:
        raise RuntimeError(f"no translations held for keys found in source: {missing_translation_keys}")
    extra_translation_keys = [k for k in TRANSLATIONS if k not in keys]
    if extra_translation_keys:
        raise RuntimeError(f"translations held for keys no longer in source: {extra_translation_keys}")

    out_dir = os.path.join(REPO, "dist", "Interface", "Translations")
    english = {k: keys[k] for k in order}
    write_translation_file(os.path.join(out_dir, "SoulsToPerks_english.txt"), english)
    print(f"english: {len(english)} keys")

    for lang in LANGS[1:]:
        translated = {k: TRANSLATIONS[k][lang] for k in order}
        write_translation_file(os.path.join(out_dir, f"SoulsToPerks_{lang}.txt"), translated)
        print(f"{lang}: {len(translated)} keys written")


if __name__ == "__main__":
    main()
