from fastapi import APIRouter, HTTPException, status
from app.schemas.item import Item, ItemCreate, ItemUpdate

router = APIRouter()

# In-memory storage (replace with database in production)
fake_items_db: dict[int, Item] = {}
next_id = 1


@router.get("/items", response_model=list[Item])
async def read_items(skip: int = 0, limit: int = 10):
    """Get all items with pagination"""
    items = list(fake_items_db.values())
    return items[skip : skip + limit]


@router.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    """Get a specific item by ID"""
    if item_id not in fake_items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return fake_items_db[item_id]


@router.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    """Create a new item"""
    global next_id
    new_item = Item(id=next_id, **item.model_dump())
    fake_items_db[next_id] = new_item
    next_id += 1
    return new_item


@router.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemUpdate):
    """Update an existing item"""
    if item_id not in fake_items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    stored_item = fake_items_db[item_id]
    update_data = item.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(stored_item, field, value)

    fake_items_db[item_id] = stored_item
    return stored_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    """Delete an item"""
    if item_id not in fake_items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    del fake_items_db[item_id]
    return None
