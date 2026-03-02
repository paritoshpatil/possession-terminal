---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - possession/models.py
  - possession/tui/screens/filter_picker.py
  - possession/tui/screens/main.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "User can press 'd' on a highlighted room in the room picker to delete it, with confirmation showing container and item counts"
    - "User can press 'd' on a highlighted container in the container picker to delete it, with confirmation showing item count"
    - "User can press 'd' on a highlighted category in the category picker to delete it, with confirmation that items lose their category (not deleted)"
    - "Confirming deletion removes the entity and reloads the item list in MainScreen"
    - "Pressing Escape or 'n' in the confirmation prompt cancels deletion without changes"
    - "After deletion, any active filter for the deleted entity is cleared and item list reloads"
  artifacts:
    - path: "possession/models.py"
      provides: "count_room_contents and count_container_items model functions"
      contains: "def count_room_contents"
    - path: "possession/tui/screens/filter_picker.py"
      provides: "Delete flow: 'd' key, inline confirmation, entity deletion"
      contains: "_delete_mode"
    - path: "possession/tui/screens/main.py"
      provides: "Updated picker calls passing db_path and kind"
      contains: "FilterPickerScreen"
  key_links:
    - from: "possession/tui/screens/filter_picker.py"
      to: "possession/models.py"
      via: "delete_room / delete_container / delete_category calls"
      pattern: "delete_room|delete_container|delete_category"
    - from: "possession/tui/screens/main.py"
      to: "possession/tui/screens/filter_picker.py"
      via: "FilterPickerScreen constructor with db_path and kind args"
      pattern: "FilterPickerScreen.*db_path"
---

<objective>
Add 'd' delete functionality inside the Room, Container, and Category filter picker modal. When the user highlights an entry and presses 'd', show an inline confirmation prompt with impact details (container/item counts for rooms, item counts for containers, category-detach note for categories). Confirmed deletion removes the entity, clears any active filter for it, and reloads the item list.

Purpose: Users accumulate stale rooms, containers, and categories over time and need a way to clean them up without leaving the TUI.
Output: Updated FilterPickerScreen with delete support, two new model count-query helpers, and updated MainScreen picker call-sites to pass db_path and kind.
</objective>

<execution_context>
@/Users/paritoshpatil/.claude/get-shit-done/workflows/execute-plan.md
@/Users/paritoshpatil/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

@possession/models.py
@possession/tui/screens/filter_picker.py
@possession/tui/screens/main.py
</context>

<interfaces>
<!-- Key contracts the executor needs. -->

From possession/models.py — existing delete functions:
```python
def delete_room(db_path: Path, room_id: int) -> None:
    """Delete a room. Cascades to containers (ON DELETE CASCADE in schema).
    Raises ValueError if room_id not found.
    """

def delete_container(db_path: Path, container_id: int) -> None:
    """Delete a container.
    Raises ValueError if not found.
    """

def delete_category(db_path: Path, category_id: int) -> None:
    """Delete a category.
    Items with this category get category_id=NULL (ON DELETE SET NULL in schema).
    Raises ValueError if not found.
    """
```

From possession/tui/screens/filter_picker.py — FilterPickerScreen constructor:
```python
def __init__(
    self,
    title: str,
    items: List[Dict],
    active_id: Optional[int] = None,
):
```

From possession/tui/screens/main.py — picker call-sites:
```python
self.app.push_screen(
    FilterPickerScreen("Room", rooms, self._filter_room_id),
    self._on_room_picked,
)
# Similarly for Container and Category
```

From possession/tui/screens/main.py — picker callbacks return type:
```python
# Callbacks receive Optional[dict] — None means no change / cancelled
# dict has 'id' and 'name' keys
def _on_room_picked(self, result: Optional[dict]) -> None:
```

Schema cascade behavior (from decisions):
- Rooms: ON DELETE CASCADE on containers -> containers deleted. Items: ON DELETE SET NULL -> items lose room_id but are NOT deleted.
- Containers: Items ON DELETE SET NULL -> items lose container_id but are NOT deleted.
- Categories: Items ON DELETE SET NULL -> items lose category_id but are NOT deleted.

NOTE: The room deletion cascade means room -> containers are deleted, and those containers' items lose container_id too (but items themselves survive via ON DELETE SET NULL on items.room_id). The count should reflect this clearly to the user.
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: Add count query helpers to models.py</name>
  <files>possession/models.py</files>
  <action>
Add two new functions to possession/models.py after the existing list_rooms/list_containers/list_categories functions:

1. `count_room_contents(db_path: Path, room_id: int) -> dict`
   - Returns `{"containers": int, "items": int}`
   - containers: COUNT(*) FROM containers WHERE room_id = ?
   - items: COUNT(*) FROM items WHERE room_id = ?
   - Use per-call connection pattern (get_connection / conn.close() in finally)
   - Use sqlite3.Row row_factory

2. `count_container_items(db_path: Path, container_id: int) -> dict`
   - Returns `{"items": int}`
   - items: COUNT(*) FROM items WHERE container_id = ?
   - Same connection pattern

Place count_room_contents after list_rooms (around line 65), and count_container_items after list_containers (around line 143). Follow the exact same connection pattern as all other model functions in this file.
  </action>
  <verify>
    <automated>cd /Users/paritoshpatil/Personal/claude-projects/possession-terminal-2 && python -c "from possession.models import count_room_contents, count_container_items; print('OK')"</automated>
  </verify>
  <done>Both functions importable; count_room_contents returns dict with 'containers' and 'items' keys; count_container_items returns dict with 'items' key</done>
</task>

<task type="auto">
  <name>Task 2: Add delete flow to FilterPickerScreen and update MainScreen call-sites</name>
  <files>possession/tui/screens/filter_picker.py, possession/tui/screens/main.py</files>
  <action>
## Part A — FilterPickerScreen changes (possession/tui/screens/filter_picker.py)

### Constructor changes
Add two new parameters after `active_id`:
- `db_path` (Path) — needed to call model functions and count queries
- `kind: str` — one of `"room"`, `"container"`, `"category"` — determines delete behavior

Store as `self._db_path` and `self._kind`. Keep `db_path` and `kind` keyword-only (they come after `active_id`). Add `from pathlib import Path` at top if not already present.

### New state in `__init__`
```python
self._delete_mode: bool = False          # True when awaiting d/y/n confirmation
self._delete_candidate: Optional[Dict] = None  # item dict being confirmed for deletion
```

### compose() changes
Add a confirmation prompt Static widget at the bottom of the `#picker-container` Vertical, below `#picker-hint`:
```python
yield Static("", id="picker-delete-confirm", classes="hidden")
```

Add CSS for it in DEFAULT_CSS:
```css
#picker-delete-confirm {
    height: auto;
    color: $text;
    text-align: center;
    background: $surface-darken-1;
    padding: 0 1;
}
```

### New method: `_get_impact_line(item: dict) -> str`
Builds the impact description string for the confirmation prompt.

```python
def _get_impact_line(self, item: dict) -> str:
    if self._kind == "room":
        from possession.models import count_room_contents
        counts = count_room_contents(self._db_path, item["id"])
        c = counts["containers"]
        i = counts["items"]
        return (
            f"This will also delete {c} container(s) and {i} item(s) will lose their room."
        )
    elif self._kind == "container":
        from possession.models import count_container_items
        counts = count_container_items(self._db_path, item["id"])
        i = counts["items"]
        return f"This will remove {i} item(s) from this container."
    else:  # category
        return "Items with this category will have their category cleared (not deleted)."
```

### Update `on_key` handler
In the existing `on_key(self, event: events.Key)` method:

**When `_delete_mode` is False:**
- Add `elif event.key == "d":` branch BEFORE the escape/j/k/enter handling
- Get the currently highlighted item from `self._filtered` using `lv.index`
- If `lv.index is None` or no items in `self._filtered`, do nothing
- Set `self._delete_candidate = self._filtered[lv.index]`
- Set `self._delete_mode = True`
- Build confirmation text: `f"Delete '{candidate['name']}'? {self._get_impact_line(candidate)} [y/n]"`
- Show `#picker-delete-confirm` (remove "hidden" class), set its `update()` to the confirmation text
- `event.prevent_default()`

**When `_delete_mode` is True:**
At the top of `on_key`, check `if self._delete_mode:` and handle these keys:
- `y`: call the appropriate delete function based on `self._kind`, catch ValueError (already gone), call `self.dismiss({"deleted": True, "id": self._delete_candidate["id"], "name": self._delete_candidate["name"]})`, `event.prevent_default()`, return
- `n` or `escape`: reset `_delete_mode = False`, `_delete_candidate = None`, hide `#picker-delete-confirm`, `event.prevent_default()`, return
- Any other key: `event.prevent_default()`, return (block all navigation while in confirm mode)

Delete dispatch in the `y` handler:
```python
if self._kind == "room":
    from possession.models import delete_room
    delete_room(self._db_path, self._delete_candidate["id"])
elif self._kind == "container":
    from possession.models import delete_container
    delete_container(self._db_path, self._delete_candidate["id"])
else:  # category
    from possession.models import delete_category
    delete_category(self._db_path, self._delete_candidate["id"])
```

The `dismiss` result dict uses key `"deleted": True` so MainScreen callbacks can distinguish a deletion from a normal selection. Normal selections are plain `{"id": ..., "name": ...}` dicts — no "deleted" key.

Also: while `_delete_mode` is True, block `j`/`k`/`enter` navigation (prevent_default and return) so the user can only respond to the confirmation.

## Part B — MainScreen changes (possession/tui/screens/main.py)

### Update all three picker call-sites to pass `db_path` and `kind`

In `action_open_room_picker`:
```python
FilterPickerScreen("Room", rooms, self._filter_room_id, db_path=self.app.db_path, kind="room")
```

In `action_open_container_picker`:
```python
FilterPickerScreen("Container", containers, self._filter_container_id, db_path=self.app.db_path, kind="container")
```

In `action_open_category_picker`:
```python
FilterPickerScreen("Category", categories, self._filter_category_id, db_path=self.app.db_path, kind="category")
```

### Update all three picker callbacks to handle `"deleted": True` results

In `_on_room_picked`, `_on_container_picked`, `_on_category_picked`, add a check BEFORE the existing toggle logic:

```python
def _on_room_picked(self, result: Optional[dict]) -> None:
    if result is None:
        return
    if result.get("deleted"):
        # Entity was deleted — clear filter if it was active, reload
        if self._filter_room_id == result["id"]:
            self._filter_room_id = None
            self._filter_room_name = None
        self._load_items()
        return
    # existing toggle logic below...
    if result["id"] == self._filter_room_id:
        ...
```

Apply the same pattern to `_on_container_picked` (checking `_filter_container_id`) and `_on_category_picked` (checking `_filter_category_id`).

## Part C — footer hint update (possession/tui/screens/main.py)

Update `_FOOTER_TEXT` to include delete hint for pickers:
```python
_FOOTER_TEXT = (
    "add: a | edit: e | delete item: d | rooms: r | containers: c | categories: t"
    " | details: enter | close: esc | quit: q"
)
```

Also update the picker's `#picker-hint` to show "d to delete" when cursor is over a non-active item. In `on_list_view_highlighted`, after the existing active-item hint logic, add:
```python
hint.update("[dim]d to delete[/dim]")
```
as the fallback (replacing the empty string `""`) so users know the shortcut exists.
  </action>
  <verify>
    <automated>cd /Users/paritoshpatil/Personal/claude-projects/possession-terminal-2 && python -c "from possession.tui.screens.filter_picker import FilterPickerScreen; from pathlib import Path; s = FilterPickerScreen('Room', [], None, db_path=Path('/tmp/test.db'), kind='room'); print('OK')"</automated>
  </verify>
  <done>FilterPickerScreen accepts db_path and kind params; pressing 'd' in the picker shows confirmation with impact line; 'y' deletes and dismisses with deleted=True; 'n'/escape cancels; MainScreen callbacks handle deleted=True by clearing filter and reloading</done>
</task>

</tasks>

<verification>
Run the app and manually open the room picker ('r'), highlight a room, press 'd' — confirmation prompt should appear with container/item counts. Press 'y' — room should be deleted and item list should reload. Repeat for container picker ('c') and category picker ('t'). For categories, confirmation should note that items lose their category, not that they are deleted.

Python import check:
```
python -c "from possession.models import count_room_contents, count_container_items; from possession.tui.screens.filter_picker import FilterPickerScreen; print('all imports OK')"
```
</verification>

<success_criteria>
- Pressing 'd' on any entry in the Room, Container, or Category picker shows an inline confirmation in the picker modal
- Room confirmation shows: container count + item count that will lose their room
- Container confirmation shows: item count that will lose their container
- Category confirmation shows: items will have category cleared, not deleted
- 'y' confirms deletion; 'n' and Escape cancel
- After deletion: picker dismisses, MainScreen clears the deleted entity's filter if active, reloads item list
- No crashes when deleting an entity that has zero containers/items
</success_criteria>

<output>
After completion, create `.planning/quick/1-add-delete-functionality-for-rooms-conta/1-SUMMARY.md` following the summary template.
</output>
