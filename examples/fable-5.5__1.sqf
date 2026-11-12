// fn_addkillreward.sqf
// выдает очки за убийство
params ["_unit"];

// обработчик вешается только на сервере, иначе очки начислятся несколько раз
if (!isServer) exitWith {};

// mpkilled срабатывает на сервере, даже если юнит локален клиенту
_unit addMPEventHandler ["MPKilled", {
    params ["_victim", "_killer", "_instigator"];
    // mpkilled выполняется на всех машинах, очки считает только сервер
    if (!isServer) exitWith {};
    // при убийстве из техники в _killer приходит техника, стрелок лежит в _instigator
    if (!isNull _instigator) then { _killer = _instigator };
    // за самоубийство очки не даем
    if (_killer isEqualTo _victim) exitWith {};
    if (isPlayer _killer) then {
        // true рассылает значение клиентам
        _killer setVariable ["pts", (_killer getVariable ["pts", 0]) + 10, true];
        // hint локальная команда, показываем ее на машине убийцы
        [format ["+10 очков, всего: %1", _killer getVariable "pts"]] remoteExec ["hint", _killer];
    };
}];
