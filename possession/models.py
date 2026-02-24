import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

from possession.db import get_connection


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

def create_room(db_path: Path, name: str) -> int:
    """Insert a new room. Returns the new row id.
    Raises sqlite3.IntegrityError on duplicate name.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute("INSERT INTO rooms (name) VALUES (?)", (name,))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def rename_room(db_path: Path, room_id: int, new_name: str) -> None:
    """Rename an existing room.
    Raises ValueError if room_id not found.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "UPDATE rooms SET name=? WHERE id=?", (new_name, room_id)
        )
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"Room {room_id} not found")
    finally:
        conn.close()


def delete_room(db_path: Path, room_id: int) -> None:
    """Delete a room. Cascades to containers (ON DELETE CASCADE in schema).
    Raises ValueError if room_id not found.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute("DELETE FROM rooms WHERE id=?", (room_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"Room {room_id} not found")
    finally:
        conn.close()


def list_rooms(db_path: Path) -> List[Dict]:
    """Return all rooms ordered by name as plain dicts."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, name, created_at FROM rooms ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Containers
# ---------------------------------------------------------------------------

def create_container(db_path: Path, name: str, room_id: int) -> int:
    """Insert a new container in a room. Returns the new row id.
    Raises sqlite3.IntegrityError on duplicate (name, room_id).
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO containers (name, room_id) VALUES (?, ?)",
            (name, room_id),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def rename_container(db_path: Path, container_id: int, new_name: str) -> None:
    """Rename an existing container.
    Raises ValueError if not found.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "UPDATE containers SET name=? WHERE id=?", (new_name, container_id)
        )
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"Container {container_id} not found")
    finally:
        conn.close()


def delete_container(db_path: Path, container_id: int) -> None:
    """Delete a container.
    Raises ValueError if not found.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM containers WHERE id=?", (container_id,)
        )
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"Container {container_id} not found")
    finally:
        conn.close()


def list_containers(
    db_path: Path, room_id: Optional[int] = None
) -> List[Dict]:
    """Return containers as plain dicts.
    If room_id is given, filter to that room only.
    """
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if room_id is not None:
            rows = conn.execute(
                "SELECT id, name, room_id, created_at FROM containers"
                " WHERE room_id=? ORDER BY name",
                (room_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, room_id, created_at FROM containers"
                " ORDER BY name"
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def create_category(db_path: Path, name: str) -> int:
    """Insert a new category. Returns the new row id."""
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO categories (name) VALUES (?)", (name,)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def rename_category(db_path: Path, category_id: int, new_name: str) -> None:
    """Rename an existing category.
    Raises ValueError if not found.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "UPDATE categories SET name=? WHERE id=?", (new_name, category_id)
        )
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"Category {category_id} not found")
    finally:
        conn.close()


def delete_category(db_path: Path, category_id: int) -> None:
    """Delete a category.
    Items with this category get category_id=NULL (ON DELETE SET NULL in schema).
    Raises ValueError if not found.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM categories WHERE id=?", (category_id,)
        )
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"Category {category_id} not found")
    finally:
        conn.close()


def list_categories(db_path: Path) -> List[Dict]:
    """Return all categories ordered by name as plain dicts."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, name, created_at FROM categories ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

def create_item(
    db_path: Path,
    name: str,
    description: Optional[str] = None,
    room_id: Optional[int] = None,
    container_id: Optional[int] = None,
    category_id: Optional[int] = None,
    purchase_date: Optional[str] = None,
    cost: Optional[float] = None,
) -> int:
    """Insert a new item. Returns the new row id.
    All fields except name are optional (NULL allowed).
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO items"
            " (name, description, room_id, container_id, category_id,"
            "  purchase_date, cost)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, description, room_id, container_id, category_id,
             purchase_date, cost),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


# Sentinel for "caller did not pass this argument" — distinct from None (which means set to NULL)
_UNSET = object()


def update_item(
    db_path: Path,
    item_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    room_id: object = _UNSET,
    container_id: object = _UNSET,
    category_id: object = _UNSET,
    purchase_date: Optional[str] = None,
    cost: Optional[float] = None,
) -> None:
    """Update any subset of item fields. Only fields explicitly passed are modified.
    For room_id, container_id, category_id: pass None to set the field to NULL.
    Raises ValueError if item_id not found.
    """
    pairs = []
    if name is not None:
        pairs.append(("name", name))
    if description is not None:
        pairs.append(("description", description))
    if room_id is not _UNSET:
        pairs.append(("room_id", room_id))
    if container_id is not _UNSET:
        pairs.append(("container_id", container_id))
    if category_id is not _UNSET:
        pairs.append(("category_id", category_id))
    if purchase_date is not None:
        pairs.append(("purchase_date", purchase_date))
    if cost is not None:
        pairs.append(("cost", cost))

    if not pairs:
        return  # nothing to update

    set_clause = ", ".join(f"{col}=?" for col, _ in pairs)
    values = [val for _, val in pairs] + [item_id]

    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            f"UPDATE items SET {set_clause} WHERE id=?", values
        )
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"Item {item_id} not found")
    finally:
        conn.close()


def delete_item(db_path: Path, item_id: int) -> None:
    """Delete an item permanently.
    Raises ValueError if item_id not found.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"Item {item_id} not found")
    finally:
        conn.close()


def list_items(
    db_path: Path,
    room_id: Optional[int] = None,
    container_id: Optional[int] = None,
    category_id: Optional[int] = None,
) -> List[Dict]:
    """Return items with joined room_name, container_name, category_name.
    Supports optional filtering by room_id, container_id, or category_id.
    """
    sql = (
        "SELECT items.id, items.name, items.description,"
        "       items.room_id, items.container_id, items.category_id,"
        "       items.purchase_date, items.cost, items.created_at,"
        "       rooms.name AS room_name,"
        "       containers.name AS container_name,"
        "       categories.name AS category_name"
        " FROM items"
        " LEFT JOIN rooms ON items.room_id = rooms.id"
        " LEFT JOIN containers ON items.container_id = containers.id"
        " LEFT JOIN categories ON items.category_id = categories.id"
    )
    conditions = []
    params = []
    if room_id is not None:
        conditions.append("items.room_id = ?")
        params.append(room_id)
    if container_id is not None:
        conditions.append("items.container_id = ?")
        params.append(container_id)
    if category_id is not None:
        conditions.append("items.category_id = ?")
        params.append(category_id)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY items.name"

    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
