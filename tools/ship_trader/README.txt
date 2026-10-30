Ship dealer catalogue
====================
python tools/ship_trader/check.py

Compiles the production catalogue, binding and input methods with the production
class declaration and UI/market doubles. Runs under x86 AddressSanitizer. Exercises
50 ships, every visible-to-catalogue mapping, rank/reputation sorting, original
market indices, selection outside the viewport, buy/double-click restrictions,
scrollbar endpoints, wheel routing and a one-ship market. SelectRow's 3D preview
and the engine's actual scrollbar rendering are not emulated by this harness.

The current layout keeps three visible rows; wheel input moves one ship per notch,
not three-item pages. The catalogue has no three-ship cap. No FLUF dependency.

In-game smoke check:
* Visit a base whose market lists at least 5 valid ship packages.
* Scroll over names, icons and the bar; drag the thumb to the last ship.
* Select a ship, scroll it out of view, then buy: verify the same hull/package.
* Check locked and unaffordable packages, double click, current ship, cancel/reopen.
* Confirm description scrolling and 3D rotation remain independent of the list.
* Check a base with 1-3 ships: no scrollbar, all its ships visible.
