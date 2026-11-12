// fn_addKillReward.sqf
// выдает очки за убийство
params ["_unit"];

_unit addMPEventHandler ["MPKilled", {
    params ["_victim", "_killer", "_instigator"];

    if (!isServer || {_victim isEqualTo _killer}) exitWith {};

    private _scorer = [_killer, _instigator] select !isNull _instigator;
    if !(isPlayer _scorer) exitWith {};

    private _pts = (_scorer getVariable ["pts", 0]) + 10;
    _scorer setVariable ["pts", _pts, true];
    [format ["+10 очков, всего: %1", _pts]] remoteExec ["hint", _scorer];
}];
