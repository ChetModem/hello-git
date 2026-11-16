# Card versions

Every card design change gets a new version number. Older files are never overwritten, so any
version can be printed again. Git history (branch `ccr-23eaa64c-ef455x`) holds every file as well.

## v1 (commit ffd1060) - current files, kept as they are
| Cards | File |
|---|---|
| Resource cards (19 each) | `catan-{brick,wood,sheep,wheat,ore}-19-cards.3mf`, banked: `finished/FINISHED-catan-{brick,sheep}-19-cards.3mf` |
| Development cards | `catan-knight-14-cards.3mf`, `catan-victory-point-5-cards.3mf`, `catan-road-building-2-cards.3mf`, `catan-year-of-plenty-2-cards.3mf`, `catan-monopoly-2-cards.3mf` |
| Building Costs x4, Longest Road, Largest Army | `catan-special-cards-6.3mf` |
| Rules legend + stand | `catan-rules-legend-with-stand.3mf` |
| Review sheet | `catan-all-cards-review.png` |

Known issues in v1 (found in the whole-set review): coloured icons sit over the white back logo on
all development cards and the 6 special cards (it can show through the 0.5 mm card); Monopoly and
Wheat icons are much lighter than the rest; three different road drawings; helmet crests drop to
dots on Largest Army; progress-card icons are the same green as their corner hexes.

## v2 gold standard: the resource cards (locked)
The five resource cards and their back are final and are the reference for every other card.
Test plate: `catan-resource-cards-v2-test.3mf` (one of each, 0.5 mm, built by `tools/v2/build_resource_test.py`).
Design rules taken from them:
1. Flat, straight-on drawing. Solid colour shapes; detail only as black cuts, never as drawn outlines.
2. One line weight: every cut and gap 0.8 mm (brick mortar 0.9 is the one deliberate exception).
3. Every outside corner and tip rounded 0.3 mm.
4. No small fiddly pieces: smallest piece in an icon about 8 mm2 (hard floor 2 mm2).
5. Even weight: about 270 mm2 of colour per icon; a shape may be lighter only when that is its nature (wheat).
6. Shared placement: tall icons end on one line (13.7 mm below centre), wide icons on another (8.5 mm), centred left-right.
7. Minimal: no faces, no text; recognisable from the outline alone.
8. One colour per icon, matching the corner hexagons. Built at final size (never shrunk after building).

## v2 - in design (previews first, files after approval)
Preview: `catan-cards-v2-preview.png`. Code: `tools/v2/`.
- Roads drawn as cobbled paths (black joints mark two staggered rows of stones, joints run through every bend):
  Road Building (crossed with a hammer) and Longest Road (one path along 5 hex edges, same road width and stone size).
  Building Costs shows the road *piece* as a silhouette.
- Building Costs: rows (piece on the left, one hexagon per resource card) - the centred-blocks layout was tried and dropped.
- Year of Plenty and Monopoly use the same card size; Monopoly's crown rests on a fan of 3 cards.
- Victory Point trophy: open handles, solid black star. Small trophies (Longest Road, Largest Army): 12.5 mm.
- Resource icons: LOCKED (`catan-resource-set-v2-locked.png`, shapes saved by `tools/v2/locked_set.py`).
  Flat, straight-on, solid shapes split by 0.8 mm black lines, 0.3 mm rounded tips, about 270 mm2 of colour each
  (wheat about 115, lighter by nature). Tall icons (pine, sheep, wheat) end on one line, wide ones (brick, ore) on another.
  - Brick: v1 wall layout rebuilt, 0.9 mm mortar.
  - Wood: pine tree, three tiers and a trunk (olive filament kept).
  - Sheep: symmetrical fleece, head and ears as one solid shape, no face, two legs.
  - Wheat: single ear of angular grains, 1.7 mm stalk.
  - Ore: two faceted rocks on an uneven base; big rock with a Y of lines and no right line; small rock with a cut
    bottom-left corner and its lower line veering off towards that corner.
  Rounds of options: `catan-resource-round3..7.png`, `catan-ore-lines-round9/10.png`, `catan-ore-small-rock-round11/12.png`.
- One card drawing everywhere (white card, black hexagon outline = a resource back with the colours swapped):
  Year of Plenty, Monopoly, Building Costs dev-card piece.
- Monopoly: crown over 3 cards. Road Building, Year of Plenty, Monopoly: white icons, green only in the corners.
- Knight helmet: no crest, rounded dome (Knight, Largest Army, legend).
- One trophy everywhere: filled handles, solid black star (Victory Point, Longest Road, Largest Army, their back).
- Backs: the original designs; Building Costs back gets three coin stacks in the ring (like the trophy back). Development and table cards go to 0.6 mm with one black layer between the colour
  and the back logo, so the logo cannot show through. Resource cards stay 0.5 mm (their icons are clear of the ring).
- Final consistency pass (`catan-cards-v2-final-review.png`): every card now uses the resource set's rules -
  0.8 mm lines and gaps everywhere (development and table cards were at 0.7), 0.3 mm rounded tips, no loose
  pieces under 2 mm2 (two chips at the Longest Road bends removed), single development icons centred halfway
  between outline and weight like the ore, Knight helmet brought down to the others' weight (327 -> 297 mm2).
  Rejected resource options removed from the card list (code kept in history).
- Development / table cards, refined against the resource rules (rounds: `catan-cards-v2-dev-round1..3.png`,
  `catan-monopoly-figure-options.png`, `catan-cards-v2-road-experiments.png`, `catan-road-building-tool-options.png`):
  - Locked: Victory Point (the one trophy, solid handles); placement rule for single icons; Building Costs without
    corner hexagons; every card drawing = white card with a solid black hexagon; Year of Plenty as it was;
    one trophy row height on all table cards, picture 4 mm above it.
  - Locked: Road Building = hammer crossed with a road of irregular, uneven cobbles (nothing left out).
    Rejected: shovel (reads as digging), pickaxe (mining / ore), hammer + shovel crossed (loses the road),
    both tools over a road (too busy).
  - Locked: Longest Road = road of evened irregular cobbles, 4 runs at 20 degrees; joints at the bends offset (never
    straight across); the middle dip's joints placed by hand and one joint nudged 1 mm to even the stones.
    Rejected: wagon wheel (too busy), straight-through bend joints, regular stagger (grid pattern).
  - Locked: Monopoly = crown just above a fan of three cards, each with its whole centre hexagon.
    Rejected: crown resting on the fan (squashed, hexagons hidden), figure behind the fan, fist holding cards,
    crown on a deck, crown alone with a hexagon jewel.
  - Locked: Year of Plenty sized by weight like every icon (its cards larger than Monopoly's; matching Monopoly's
    card size would leave it at ~106 mm2). Size options: `catan-year-of-plenty-size-options.png`.
  - Resource sheep updated: legs and fleece raised so it is centred on its weight (feet still on the shared line).
    Fix: the first version of this lost the black split under the chin (the head did not move down with the taller
    fleece); the head now moves with it and the split is back (`catan-sheep-chin-fix.png`). Every resource icon was
    then checked against its approved version: all identical, and the cards use them unchanged.
  - Building Costs: original Catan piece shapes kept (clearer, match the rulebook, work for anyone printing the files
    without this set's pieces); pieces right-aligned so every row has the same gap before its hexagons; road piece
    standing near vertical (80 degrees). The set's own pieces were tried (`catan-building-costs-own-pieces.png`) and dropped.
  - Knight helmet brought to the set's weight (275 mm2).
  - Victory Point sized where it stands on the tall line, so it sits inside the back ring like the others (255 mm2).
  - Longest Road's road raised so its middle is level with Largest Army's helmets (trophy row unchanged).
  - Largest Army helmet spacing kept (suits the road's zig-zag).
  - Building Costs: road piece back at its 30 degree angle; pieces centred on their weight and spaced to where they
    look solid (`catan-building-costs-alignment.png`: outer edges / weight-centred / optical - optical used).
  - Full-set review: in-between icons (Monopoly, Road Building) centred on their weight, like the sheep; Road Building
    sized where it stands so it stays inside the ring (`catan-weight-centring.png`: before / after for each).
    Road Building: any stone over 1.5 x the median gets one more joint across the road (split the one long plank).
  - Backs: every line at the ring's 1.6 mm (development rings, trophy outline); coin stacks drawn at 1.35 mm so the
    thicker lines don't crowd the gaps between coins.
- Test: `catan-backs-showthrough-test.3mf` - Knight and Victory Point at 0.5 mm (left) and 0.6 mm (right).
