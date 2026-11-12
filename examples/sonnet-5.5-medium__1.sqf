// fn_addkillreward.sqf
// выдает очки за убийство
// вызывать только на сервере

// защита: на клиенте функция ничего не делает
if (!isserver) exitwith {};

// проверка аргумента
params [["_unit", objnull, [objnull]]];
if (isnull _unit) exitwith {};

// защита от повторной навески обработчика на тот же юнит
if (_unit getvariable ["kr_hooked", false]) exitwith {};
_unit setvariable ["kr_hooked", true];

// mpkilled срабатывает на всех машинах, а не только там, где юнит local
_unit addmpeventhandler ["mpkilled", {
    params ["_victim", "_killer", "_instigator"];

    // начисляем очки только на сервере
    if (!isserver) exitwith {};

    // инстигатор точнее killer: тот, кто реально стрелял
    private _k = if (isnull _instigator) then {_killer} else {_instigator};

    // если убийцей оказалась техника, берем командира экипажа
    if (!(_k iskindof "camanbase")) then {_k = effectivecommander _k};

    // не даем очки за самоубийство, пустого убийцу и ботов
    if (isnull _k || {_k isequalto _victim} || {!isplayer _k}) exitwith {};

    private _pts = (_k getvariable ["pts", 0]) + 10;
    // третий параметр true: значение видят клиенты (скорборд и т.п.)
    _k setvariable ["pts", _pts, true];

    // hint локальная команда, на сервере игроку он не покажется, шлем клиенту
    (format ["+10 очков, всего: %1", _pts]) remoteexec ["hint", _k];
}];
