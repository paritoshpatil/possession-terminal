# possession

A terminal-based home inventory manager. Track what you own, where it is, and what it cost — entirely from the keyboard.

```
▗▄▄▖  ▗▄▖  ▗▄▄▖ ▗▄▄▖▗▄▄▄▖ ▗▄▄▖ ▗▄▄▖▗▄▄▄▖ ▗▄▖ ▗▖  ▗▖
▐▌ ▐▌▐▌ ▐▌▐▌   ▐▌   ▐▌   ▐▌   ▐▌     █  ▐▌ ▐▌▐▛▚▖▐▌
▐▛▀▘ ▐▌ ▐▌ ▝▀▚▖ ▝▀▚▖▐▛▀▀▘ ▝▀▚▖ ▝▀▚▖  █  ▐▌ ▐▌▐▌ ▝▜▌
▐▌   ▝▚▄▞▘▗▄▄▞▘▗▄▄▞▘▐▙▄▄▖▗▄▄▞▘▗▄▄▞▘▗▄█▄▖▝▚▄▞▘▐▌  ▐▌
```

## Installation

```bash
pip install possession-terminal
```

Requires Python 3.9+.

## Usage

```bash
possession
```

**Options:**

| Flag | Description |
|------|-------------|
| `--db PATH` | Use a specific database file |
| `--transparent` | Use terminal native background for this session |

```bash
# Use a custom database location
possession --db ~/Documents/my-inventory.db

# Use an environment variable instead
POSSESSION_DB=~/Documents/my-inventory.db possession

# Transparent background (blends with your terminal theme)
possession --transparent
```

The database is created automatically at `~/.possession/possession.db` on first launch.

---

## Navigation

possession uses Vim-style keybindings throughout.

### Main screen

| Key | Action |
|-----|--------|
| `j` / `k` | Move down / up |
| `g g` | Jump to top |
| `G` | Jump to bottom |
| `h` / `l` | Scroll left / right |
| `Enter` | Toggle detail panel |
| `q` / `Esc` | Quit |

### Managing items

| Key | Action |
|-----|--------|
| `a` | Quick-add a new item |
| `e` | Edit selected item |
| `d` | Delete selected item |

### Filtering

| Key | Action |
|-----|--------|
| `/` | Text search (filters name, description, location, category live as you type) |
| `r` | Filter by room |
| `c` | Filter by container |
| `t` | Filter by category |

All filters compose — active filters are shown as tags in the stats bar. Select the same item again in a picker to clear that filter.

### Other

| Key | Action |
|-----|--------|
| `X` | Open theme picker |

---

## Quick-add

Press `a` to open quick-add. Items are entered as a slash-separated string:

```
name / description / room / container / category / date / cost
```

Only the name is required. Fields can be omitted from the right:

```
Monitor
Monitor / Dell 27" 4K
Monitor / Dell 27" 4K / Office
Monitor / Dell 27" 4K / Office / Desk / Electronics / 2024-03-01 / 349.99
```

If the room or container doesn't exist yet, possession will prompt you to create it before saving.

---

## Detail panel

Press `Enter` on any item to open the detail panel on the right. It shows all fields for the selected item and updates live as you move the cursor.

---

## Stats bar

The stats bar at the top of the screen shows four aggregate values:

```
Items     Rooms     Containers     Value
42        8         12             $1,240.00
```

When filters are active, the item count reflects the filtered set and shows the active filter tags.

---

## Themes

Press `X` to open the theme picker. Navigate with `j`/`k`, press `Enter` to confirm. The theme previews live as you move through the list. Press `Esc` to revert.

Press `t` inside the picker to toggle transparent background mode.

**10 built-in themes:**

| Theme | Style |
|-------|-------|
| `catppuccin-mocha` | Soft purples and pastels (default) |
| `dracula` | Purple and pink on dark grey |
| `tokyo-night` | Cool blues and violets |
| `nord` | Arctic blues and whites |
| `rose-pine` | Muted rosewood and iris |
| `one-dark` | Atom-inspired blues and purples |
| `kanagawa` | Warm Japanese ink palette |
| `gruvbox` | Retro amber and green on warm grey |
| `monokai` | Vivid green and pink on near-black |
| `solarized-dark` | Classic precision-designed palette |

Your selected theme and transparent preference are saved to the database and restored on next launch.

---

## Currency formatting

Costs are formatted using your system locale — currency symbol, decimal separator, and thousands grouping are all applied automatically. On an Indian locale you'll see `₹1,23,456.00`; on a US locale `$1,234.56`; on a German locale `1.234,56 €`.

---

## Data

All data is stored in a single SQLite file at `~/.possession/possession.db`. To back up your inventory, copy that file. To move it to another machine, copy the file there and point possession at it with `--db`.

---

## License

MIT
