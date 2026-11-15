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
- Roads drawn as map roads (white edge lines, dashed centre line): Road Building (crossed with a hammer) and Longest Road
  (one continuous road along 5 hex edges). Building Costs shows the road *piece* as a silhouette, like the settlement and city.
- One card drawing everywhere (white card, black hexagon outline = a resource back with the colours swapped):
  Year of Plenty, Monopoly, Building Costs dev-card piece.
- Monopoly: crown over 3 cards. Road Building, Year of Plenty, Monopoly: white icons, green only in the corners.
- Knight helmet: no crest, rounded dome (Knight, Largest Army, legend).
- One trophy everywhere: filled handles, solid black star (Victory Point, Longest Road, Largest Army, their back).
- Ore: two peaks with a ridge line for depth; the ridge has a slight zag half-way down. Wheat: unchanged (v1).
- Backs: the original designs; Building Costs back gets a coin purse in the ring (like the trophy back). Development and table cards go to 0.6 mm with one black layer between the colour
  and the back logo, so the logo cannot show through. Resource cards stay 0.5 mm (their icons are clear of the ring).
- Test: `catan-backs-showthrough-test.3mf` - Knight and Victory Point at 0.5 mm (left) and 0.6 mm (right).
