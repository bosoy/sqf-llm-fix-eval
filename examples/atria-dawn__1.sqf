// fn_addkillreward.sqf
// выдает очки за убийство
params ["_unit"];

_unit addEventHandler ["Killed", {
    params ["_victim", "_killer"];
    if (isPlayer _killer) then {
        // третий параметр true: очки рассылаются всем машинам и сохраняются для JIP
        _killer setVariable ["pts", (_killer getVariable ["pts", 0]) + 10, true];
        // hint локален, на сервере его никто не увидит - выполняем на машине убийцы
        (format ["+10 очков, всего: %1", _killer getVariable "pts"]) remoteExec ["hint", _killer];
    };
}];
