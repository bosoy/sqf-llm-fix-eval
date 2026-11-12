// fn_addkillreward.sqf
// выдает очки за убийство
params ["_unit"];

_unit addEventHandler ["Killed", {
    params ["_victim", "_killer"];
    if (isPlayer _killer) then {
        _killer setVariable ["pts", (_killer getVariable ["pts", 0]) + 10];
        hint format ["+10 очков, всего: %1", _killer getVariable "pts"];
    };
}];
