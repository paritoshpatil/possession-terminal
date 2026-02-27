---
phase: 04-foundation-flat-list-visual-chrome
plan: "02"
subsystem: ui

tags: [textual, tui, splash-screen, transparent-bg, quickadd]

# Dependency graph
requires:
  - phase: 04-01
    provides: Flat-list MainScreen (VIEW-01, TOPBAR-01) as the base screen that SplashScreen transitions into

provides:
  - SplashScreen with ASCII art — pushes on launch, any key switches to MainScreen (SPSH-01)
  - --transparent CLI flag wired through __main__.py -> PossessionApp -> CSS selection (THEME-01)
  - Persistent QuickAddBar format label above input field (QADD-04)

affects: [05-detail-panel, future-phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "switch_screen(MainScreen()) used in SplashScreen.on_key to atomically replace splash with main — avoids DataTable rendering behind transparent splash"
    - "Instance-level self.CSS override in __init__ (after super().__init__()) to select between two CSS blocks based on constructor arg — class-level attribute is overridden at compose time"
    - "Two-line widget pattern: Static label (height:1) + borderless Input (height:1) stacked inside a height:2 container widget"

key-files:
  created:
    - possession/tui/screens/splash.py
  modified:
    - possession/tui/app.py
    - possession/__main__.py
    - possession/tui/widgets/quickadd.py

key-decisions:
  - "switch_screen(MainScreen()) used in SplashScreen instead of pop_screen() — prevents DataTable rendering behind transparent splash background"
  - "self.CSS instance override (not class-level CSS attribute) used to toggle transparent vs default theme — simpler than CSS class toggling"
  - "Input border removed (border: none, height: 1) to fit label + input within QuickAddBar height: 2 — avoids clipping"
  - "QUICKADD_FORMAT_HINT constant defined at module level for easy reference in compose()"

patterns-established:
  - "Screen transition pattern: push only splash on mount, use switch_screen in on_key to atomically swap to main"
  - "Conditional CSS via self.CSS instance attribute: set in __init__ after super().__init__() based on constructor args"
  - "Compact widget layout: remove Input border + set height:1 to achieve dense docked bars"

requirements-completed: [SPSH-01, THEME-01, QADD-04]

# Metrics
duration: 6min
completed: 2026-02-25
---

# Phase 4 Plan 02: Visual Chrome (Splash, Transparent, QuickAdd Label) Summary

**SplashScreen with ASCII art on launch, --transparent CLI flag for terminal-native backgrounds, and persistent QuickAddBar format label — all wired into the flat-list app from Plan 01.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-02-25T04:42:06Z
- **Completed:** 2026-02-25T04:47:49Z
- **Tasks:** 2 auto + 1 human-verify checkpoint
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments
- SplashScreen shows ASCII "POSSESSION" art on every launch; any key atomically switches to flat-list MainScreen
- `--transparent` flag accepted by CLI and switches PossessionApp CSS to a transparent-background variant
- QuickAddBar now shows persistent format label "name / description / room / container / category / date / cost" above the input at all times while bar is open
- All Phase 4 requirements met: VIEW-01, TOPBAR-01 (Plan 01) + SPSH-01, THEME-01, QADD-04 (this plan)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SplashScreen and wire transparent flag** - `a299bc1` (feat)
2. **Task 2: Add persistent format label to QuickAddBar** - `006b328` (feat)
3. **Task 2 layout fix: Fix QuickAddBar layout clipping** - `047b97b` (feat)
4. **Task 1 fix: Hide MainScreen behind splash until dismissed** - `9e56113` (fix)
5. **Task 3: Human checkpoint approved** — no commit (verification only)

## Files Created/Modified
- `possession/tui/screens/splash.py` - SplashScreen with ASCII art constant, on_key calls switch_screen(MainScreen())
- `possession/tui/app.py` - Added TITLE, _CSS_DEFAULT/_CSS_TRANSPARENT class attrs, transparent constructor param, self.CSS instance override, on_mount pushes only SplashScreen
- `possession/__main__.py` - Added --transparent argparse flag, passes args.transparent to PossessionApp
- `possession/tui/widgets/quickadd.py` - Added QUICKADD_FORMAT_HINT constant, Static label in compose(), height:2 widget, borderless height:1 inputs

## Decisions Made
- **switch_screen vs pop_screen in SplashScreen:** Initial implementation used `pop_screen()` with MainScreen pre-loaded in the stack. A deviation fix (9e56113) changed this to push only SplashScreen on mount and use `switch_screen(MainScreen())` in on_key — this prevents DataTable rendering behind the transparent splash background.
- **self.CSS instance override:** Setting `self.CSS` after `super().__init__()` overrides the class-level CSS attribute at compose time — simpler than the alternative CSS class toggle approach (`.transparent-mode`).
- **Input border removal:** To fit label + input within `height: 2`, the Input widgets needed `border: none` and `height: 1` to override Textual's default `height: 3` for Input widgets.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] DataTable renders behind transparent splash background**
- **Found during:** Task 1 (post-verify visual testing)
- **Issue:** on_mount pushed both MainScreen (bottom) and SplashScreen (top). DataTable in MainScreen rendered through the transparent SplashScreen background, causing visual bleed.
- **Fix:** Changed on_mount to push only SplashScreen. SplashScreen.on_key now calls `switch_screen(MainScreen())` instead of `pop_screen()` — atomically replaces splash with main.
- **Files modified:** possession/tui/app.py, possession/tui/screens/splash.py
- **Verification:** Splash shows clean ASCII art with no table bleed; any key transitions to full flat list.
- **Committed in:** 9e56113 (fix commit)

**2. [Rule 1 - Bug] QuickAddBar label + input clipped (layout overflow)**
- **Found during:** Task 2 (post-verify visual testing)
- **Issue:** Textual's default Input height is 3 (including border). With `QuickAddBar height: 2` and a label taking 1 line, only 1 line remained for Input — border caused clipping.
- **Fix:** Added `border: none; height: 1; background: $surface-darken-1` to `#quickadd-input` and `#quickadd-confirm` CSS rules. Borderless inputs fit cleanly within the 2-line container.
- **Files modified:** possession/tui/widgets/quickadd.py
- **Verification:** Label and input both visible without clipping; typing works correctly.
- **Committed in:** 047b97b (feat commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — visual rendering bugs)
**Impact on plan:** Both fixes were required for correct visual behavior. No scope creep.

## Issues Encountered
None beyond the two auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 4 fully complete: flat-list MainScreen (VIEW-01, TOPBAR-01), SplashScreen (SPSH-01), transparent flag (THEME-01), QuickAddBar label (QADD-04)
- Phase 5 (detail panel) can proceed — `on_data_table_row_selected()` is a no-op stub in MainScreen, ready for Phase 5 to wire detail panel display

---
*Phase: 04-foundation-flat-list-visual-chrome*
*Completed: 2026-02-25*

## Self-Check: PASSED

- 04-02-SUMMARY.md: FOUND
- Commit a299bc1 (Task 1 - SplashScreen + transparent flag): FOUND
- Commit 006b328 (Task 2 - QuickAddBar label): FOUND
- Commit 047b97b (Task 2 fix - layout): FOUND
- Commit 9e56113 (Task 1 fix - MainScreen hidden): FOUND
