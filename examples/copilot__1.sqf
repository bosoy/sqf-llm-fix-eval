// fn_addkillreward.sqf
// выдает очки за убийство
params ["_unit"];
_unit addEventHandler ["Killed", {
    params ["_victim", "_killer"];
    if (!isNull _killer && {isPlayer _killer}) then {
        private _pts = (_killer getVariable ["pts", 0]) + 10;
        _killer setVariable ["pts", _pts];
        // показываем сообщение только убийце
        [format ["+10 очков, всего: %1", _pts]] remoteExec ["hint", _killer];
    };
}];
