import pytest
from pathlib import Path
from possession.db import init_db
from possession.models import (
    create_room, rename_room, delete_room, list_rooms,
    create_container, rename_container, delete_container, list_containers,
    create_category, rename_category, delete_category, list_categories,
    create_item, list_items,
)


@pytest.fixture
def db_path(tmp_path):
    p = tmp_path / "test.db"
    init_db(str(p))
    return p


# ---------------------------------------------------------------------------
# Room tests
# ---------------------------------------------------------------------------

def test_create_room(db_path):
    rid = create_room(db_path, "Garage")
    rooms = list_rooms(db_path)
    assert len(rooms) == 1
    assert rooms[0]["name"] == "Garage"
    assert rooms[0]["id"] == rid


def test_rename_room(db_path):
    rid = create_room(db_path, "Old Name")
    rename_room(db_path, rid, "New Name")
    assert list_rooms(db_path)[0]["name"] == "New Name"


def test_delete_room(db_path):
    rid = create_room(db_path, "Temp Room")
    delete_room(db_path, rid)
    assert list_rooms(db_path) == []


def test_delete_room_cascades_containers(db_path):
    rid = create_room(db_path, "Room")
    create_container(db_path, "Box", rid)
    delete_room(db_path, rid)
    assert list_containers(db_path) == []


# ---------------------------------------------------------------------------
# Container tests
# ---------------------------------------------------------------------------

def test_create_container(db_path):
    rid = create_room(db_path, "Room")
    cid = create_container(db_path, "Shelf", rid)
    containers = list_containers(db_path, rid)
    assert len(containers) == 1
    assert containers[0]["name"] == "Shelf"
    assert containers[0]["id"] == cid


def test_rename_container(db_path):
    rid = create_room(db_path, "Room")
    cid = create_container(db_path, "Old", rid)
    rename_container(db_path, cid, "New")
    assert list_containers(db_path, rid)[0]["name"] == "New"


def test_delete_container(db_path):
    rid = create_room(db_path, "Room")
    cid = create_container(db_path, "Box", rid)
    delete_container(db_path, cid)
    assert list_containers(db_path, rid) == []


def test_list_containers_filtered_by_room(db_path):
    rid1 = create_room(db_path, "Room A")
    rid2 = create_room(db_path, "Room B")
    create_container(db_path, "Box A", rid1)
    create_container(db_path, "Box B", rid2)
    result = list_containers(db_path, rid1)
    assert len(result) == 1
    assert result[0]["name"] == "Box A"


# ---------------------------------------------------------------------------
# Category tests
# ---------------------------------------------------------------------------

def test_create_category(db_path):
    catid = create_category(db_path, "Electronics")
    cats = list_categories(db_path)
    assert len(cats) == 1
    assert cats[0]["name"] == "Electronics"
    assert cats[0]["id"] == catid


def test_rename_category(db_path):
    catid = create_category(db_path, "Old Cat")
    rename_category(db_path, catid, "New Cat")
    assert list_categories(db_path)[0]["name"] == "New Cat"


def test_delete_category_nulls_items(db_path):
    rid = create_room(db_path, "Room")
    catid = create_category(db_path, "Cat")
    create_item(db_path, "Widget", category_id=catid)
    delete_category(db_path, catid)
    items = list_items(db_path)
    assert items[0]["category_id"] is None


# ---------------------------------------------------------------------------
# Item tests
# ---------------------------------------------------------------------------

def test_create_item_all_fields(db_path):
    rid = create_room(db_path, "Room")
    cid = create_container(db_path, "Box", rid)
    catid = create_category(db_path, "Tools")
    create_item(db_path, "Hammer", "Heavy hammer", rid, cid, catid, "2024-01-01", 29.99)
    items = list_items(db_path)
    assert items[0]["name"] == "Hammer"
    assert items[0]["description"] == "Heavy hammer"
    assert items[0]["purchase_date"] == "2024-01-01"
    assert items[0]["cost"] == 29.99


def test_create_item_name_only(db_path):
    create_item(db_path, "Mystery Item")
    items = list_items(db_path)
    assert len(items) == 1
    assert items[0]["name"] == "Mystery Item"
    assert items[0]["room_id"] is None


def test_list_items_includes_joined_names(db_path):
    rid = create_room(db_path, "Kitchen")
    cid = create_container(db_path, "Drawer", rid)
    catid = create_category(db_path, "Utensils")
    create_item(db_path, "Spoon", room_id=rid, container_id=cid, category_id=catid)
    items = list_items(db_path)
    assert items[0]["room_name"] == "Kitchen"
    assert items[0]["container_name"] == "Drawer"
    assert items[0]["category_name"] == "Utensils"


def test_list_items_filtered_by_room(db_path):
    rid1 = create_room(db_path, "Bedroom")
    rid2 = create_room(db_path, "Office")
    create_item(db_path, "Pillow", room_id=rid1)
    create_item(db_path, "Laptop", room_id=rid2)
    result = list_items(db_path, room_id=rid1)
    assert len(result) == 1
    assert result[0]["name"] == "Pillow"
