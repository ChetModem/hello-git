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
  - Ore: two faceted rocks on an uneven base; small rock with its original lines, big rock with a Y of lines and no right line.
  Rounds of options: `catan-resource-round3..7.png`, `catan-ore-lines-round9/10.png`.
- One card drawing everywhere (white card, black hexagon outline = a resource back with the colours swapped):
  Year of Plenty, Monopoly, Building Costs dev-card piece.
- Monopoly: crown over 3 cards. Road Building, Year of Plenty, Monopoly: white icons, green only in the corners.
- Knight helmet: no crest, rounded dome (Knight, Largest Army, legend).
- One trophy everywhere: filled handles, solid black star (Victory Point, Longest Road, Largest Army, their back).
- Backs: the original designs; Building Costs back gets three coin stacks in the ring (like the trophy back). Development and table cards go to 0.6 mm with one black layer between the colour
  and the back logo, so the logo cannot show through. Resource cards stay 0.5 mm (their icons are clear of the ring).
- Test: `catan-backs-showthrough-test.3mf` - Knight and Victory Point at 0.5 mm (left) and 0.6 mm (right).
