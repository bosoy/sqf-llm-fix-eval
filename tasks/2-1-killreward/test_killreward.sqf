// test_killreward.sqf
// запуск из debug-консоли: [] execVM "test_killreward.sqf"
// запускать в редакторе или на хосте, не на выделенном сервере (нужен selectplayer)

// заполняются руками после прогона
private _manualFails = 0;  // ловушки 4-5: hint у клиента и синхронизация, проверены глазами на втором клиенте
private _scriptErrors = 0; // число окон -showscripterrors за прогон

// путь к проверяемой функции (версия от модели)
private _fnPath = "fn_addKillReward.sqf";
private _fn = compile preprocessFileLineNumbers _fnPath;

private _orig = player;
private _pos = getPos _orig;
private _grpW = createGroup west;
private _grpE = createGroup east;
private _results = [];

// убийца: юнит, в которого переключаемся, чтобы isplayer был true
private _killer = _grpW createUnit ["B_Soldier_F", _pos vectorAdd [5, 0, 0], [], 0, "NONE"];
selectPlayer _killer;

// запуск одного сценария: вешаем обработчик, обнуляем очки, убиваем жертву, возвращаем очки убийцы
private _run = {
    params ["_victim", "_killerObj", "_instigator"];
    [_victim] call _fn;
    _killer setVariable ["pts", 0, true];
    _victim setDamage [1, true, _killerObj, _instigator];
    sleep 1;
    _killer getVariable ["pts", 0]
};

// 0. контроль: убийца пешком, враг (ожидаем +10, иначе правка сломала базовый случай)
private _v0 = _grpE createUnit ["O_Soldier_F", _pos vectorAdd [10, 0, 0], [], 0, "NONE"];
_results pushBack ["контроль (пешком, враг)", 10, [_v0, _killer, _killer] call _run];

// 1. убийство из техники: в событии killer это машина, instigator это стрелок
private _veh = createVehicle ["B_MRAP_01_F", _pos vectorAdd [0, 10, 0], [], 0, "NONE"];
_killer moveInDriver _veh;
private _v1 = _grpE createUnit ["O_Soldier_F", _pos vectorAdd [10, 5, 0], [], 0, "NONE"];
_results pushBack ["убийство из техники", 10, [_v1, _veh, _killer] call _run];
moveOut _killer;

// 2. тимкилл: жертва своей стороны (ожидаем 0)
private _v2 = _grpW createUnit ["B_Soldier_F", _pos vectorAdd [10, 10, 0], [], 0, "NONE"];
_results pushBack ["тимкилл", 0, [_v2, _killer, _killer] call _run];

// 3. самоубийство: жертва и убийца один юнит (ожидаем 0), идет последним
_results pushBack ["самоубийство", 0, [_killer, _killer, _killer] call _run];

// возвращаемся в своего юнита и чистим тестовые объекты
selectPlayer _orig;
{deleteVehicle _x} forEach [_v0, _v1, _v2, _veh, _killer];

// сводка
private _autoFails = 0;
private _lines = [];
{
    _x params ["_name", "_expected", "_actual"];
    private _ok = _expected isEqualTo _actual;
    if (!_ok) then {_autoFails = _autoFails + 1};
    _lines pushBack format ["%1: ожидалось %2, получено %3 - %4", _name, _expected, _actual, ["ошибка", "ок"] select _ok];
} forEach _results;

private _total = _autoFails + _manualFails + _scriptErrors;
_lines pushBack format ["авто-провалы: %1 из %2", _autoFails, count _results];
_lines pushBack format ["ручные провалы: %1", _manualFails];
_lines pushBack format ["ошибки скрипта: %1", _scriptErrors];
_lines pushBack format ["итого ошибок: %1", _total];

{systemChat _x} forEach _lines;
copyToClipboard (_lines joinString endl);
hint (_lines joinString "\n");
