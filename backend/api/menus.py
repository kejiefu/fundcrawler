from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from database import get_db
from models import Menu, User
from schemas import MenuResponse, MenuCreate, MenuUpdate
from auth import get_current_active_user, check_superuser_permission

router = APIRouter(prefix="/api/menus", tags=["Menus"])

async def get_menu_by_id(db: AsyncSession, menu_id: int) -> Menu:
    """Get menu object by ID"""
    result = await db.execute(select(Menu).where(Menu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu

def build_menu_tree(menus: List[Menu]) -> List[dict]:
    """Build menu list to tree structure, return dictionary list"""
    menu_dicts = []
    for menu in menus:
        menu_dict = {
            "id": menu.id,
            "name": menu.name,
            "path": menu.path,
            "icon": menu.icon,
            "parent_id": menu.parent_id,
            "order": menu.order,
            "is_active": menu.is_active,
            "permission": menu.permission,
            "created_at": menu.created_at,
            "updated_at": menu.updated_at,
            "children": []
        }
        menu_dicts.append(menu_dict)
    
    menu_dict_map = {menu["id"]: menu for menu in menu_dicts}
    root_menus = []
    
    for menu in menu_dicts:
        if menu["parent_id"] is None:
            root_menus.append(menu)
        elif menu["parent_id"] in menu_dict_map:
            menu_dict_map[menu["parent_id"]]["children"].append(menu)
    
    def sort_children(menu_list):
        menu_list.sort(key=lambda x: x["order"])
        for menu in menu_list:
            if menu["children"]:
                sort_children(menu["children"])
        return menu_list
    
    return sort_children(root_menus)

@router.get("/", response_model=List[MenuResponse], summary="Get menu list")
async def get_menus(
    db: AsyncSession = Depends(get_db)
) -> List[MenuResponse]:
    """Get all menus, return tree structure (public interface)"""
    result = await db.execute(select(Menu).where(Menu.is_active == True))
    menus = result.scalars().all()
    return build_menu_tree(list(menus))

@router.get("/all", response_model=List[MenuResponse], summary="Get all menus (including disabled)")
async def get_all_menus(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[MenuResponse]:
    """Get all menus including disabled, admin only"""
    check_superuser_permission(current_user)
    
    result = await db.execute(select(Menu))
    menus = result.scalars().all()
    return build_menu_tree(list(menus))

@router.get("/{menu_id}", response_model=MenuResponse, summary="Get single menu")
async def get_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MenuResponse:
    """Get single menu details"""
    return await get_menu_by_id(db, menu_id)

@router.post("/", response_model=MenuResponse, status_code=status.HTTP_201_CREATED, summary="Create menu")
async def create_menu(
    menu_data: MenuCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MenuResponse:
    """Create new menu (admin only)"""
    check_superuser_permission(current_user)
    
    if menu_data.parent_id is not None:
        await get_menu_by_id(db, menu_data.parent_id)
    
    new_menu = Menu(
        name=menu_data.name,
        path=menu_data.path,
        icon=menu_data.icon,
        parent_id=menu_data.parent_id,
        order=menu_data.order,
        is_active=menu_data.is_active,
        permission=menu_data.permission
    )
    
    db.add(new_menu)
    await db.commit()
    await db.refresh(new_menu)
    
    return new_menu

@router.put("/{menu_id}", response_model=MenuResponse, summary="Update menu")
async def update_menu(
    menu_id: int,
    menu_data: MenuUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MenuResponse:
    """Update menu info (admin only)"""
    check_superuser_permission(current_user)
    
    menu = await get_menu_by_id(db, menu_id)
    
    if menu_data.name is not None:
        menu.name = menu_data.name
    if menu_data.path is not None:
        menu.path = menu_data.path
    if menu_data.icon is not None:
        menu.icon = menu_data.icon
    if menu_data.parent_id is not None:
        if menu_data.parent_id != menu_id:
            await get_menu_by_id(db, menu_data.parent_id)
        menu.parent_id = menu_data.parent_id
    if menu_data.order is not None:
        menu.order = menu_data.order
    if menu_data.is_active is not None:
        menu.is_active = menu_data.is_active
    if menu_data.permission is not None:
        menu.permission = menu_data.permission
    
    await db.commit()
    await db.refresh(menu)
    
    return menu

@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete menu")
async def delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """Delete menu (admin only)"""
    check_superuser_permission(current_user)
    
    menu = await get_menu_by_id(db, menu_id)
    
    result = await db.execute(select(Menu).where(Menu.parent_id == menu_id))
    children = result.scalars().all()
    if children:
        raise HTTPException(status_code=400, detail="Menu has children, cannot delete")
    
    await db.delete(menu)
    await db.commit()
