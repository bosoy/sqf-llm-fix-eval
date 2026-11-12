// fn_addkillreward.sqf
// выдает очки за убийство
params ["_unit"];

_unit addEventHandler ["Killed", {
    params ["_victim", "_killer"];

    // если убил экипаж техники, очки получает тот, кто командует машиной
    if (!isPlayer _killer && {_killer isKindOf "AllVehicles"}) then {
        _killer = effectiveCommander _killer;
    };

    // очки только живому игроку и не за самоубийство
    if (isPlayer _killer && {_killer != _victim}) then {
        private _pts = (_killer getVariable ["pts", 0]) + 10;
        _killer setVariable ["pts", _pts];

        // hint локальная команда, поэтому выполняем ее на клиенте игрока
        [format ["+10 очков, всего: %1", _pts]] remoteExec ["hint", _killer];
    };
}];
