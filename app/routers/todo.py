from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status

todo_router = APIRouter(tags=["Todo Management"])


@todo_router.get('/todos', response_model=list[TodoResponse])
def get_todos(db:SessionDep, user:AuthDep):
    return user.todos

@todo_router.get('/todo/{id}', response_model=TodoResponse)
def get_todo_by_id(id:int, db:SessionDep, user:AuthDep):
    todo = db.exec(select(Todo).where(Todo.id==id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return todo

@todo_router.post('/todos', response_model=TodoResponse)
def create_todo(db:SessionDep, user:AuthDep, todo_data:TodoCreate):
    todo = Todo(text=todo_data.text, user_id=user.id)
    try:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating an item",
        )

@todo_router.put('/todo/{id}', response_model=TodoResponse)
def update_todo(id:int, db:SessionDep, user:AuthDep, todo_data:TodoUpdate):
    todo = db.exec(select(Todo).where(Todo.id==id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    if todo_data.text:
        todo.text = todo_data.text
    if todo_data.done:
        todo.done = todo_data.done
    try:
        db.add(todo)
        db.commit()
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while updating an item",
        )

@todo_router.delete('/todo/{id}', status_code=status.HTTP_200_OK)
def delete_todo(id:int, db:SessionDep, user:AuthDep):

    todo = db.exec(select(Todo).where(Todo.id==id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    try:
        db.delete(todo)
        db.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while deleting an item",
        )
        
@todo_router.post('/category', status_code=status.HTTP_201_CREATED)
def create_category(db:SessionDep, user:AuthDep, category_data:CategoryCreate):
    category = Category(user_id=user.id, text=category_data.text)
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return {"message" : f"{category.text} category created!"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating an category"
        )

@todo_router.post('todo/{todo_id}/category/{cat_id}', status_code=status.HTTP_200_OK)
def add_todo(db:SessionDep, user:AuthDep, todo_id:int, cat_id:int):
    todo = db.exec(select(Todo).where(Todo.id==todo_id, Todo.user_id==user.id)).one_or_none()
    category = db.exec(select(Category).where(Category.id==cat_id, Category.user_id==user.id)).one_or_none()
    
    if not todo or category:
        raise HTTPException(
                status_code=status.HTTP_501_NOT_FOUND,
            detail="Todo or Category not found",
        )
    try:
        todo_category = TodoCategory(todo_id=todo.id, category_id=category.id)
        db.add(todo_category)
        db.commit()
        return {"message" : f"{todo.text} added to {category.text} category!"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while adding todo to category"
        )
        

    
@todo_router.delete('todo/{todo_id}/category/{cat_id}', status_code=status.HTTP_200_OK)
def delete_todo_from_category( db:SessionDep, user:AuthDep, todo_id:int, cat_id:int):

    todo_cat = db.exec(select(TodoCategory).where(TodoCategory.todo_id==todo_id, TodoCategory.category_id==cat_id )).one_or_none()
    if not todo_cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="not found",
        )
    try:
        db.delete(todo_cat)
        db.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while deleting an item",
        )

@todo_router.get('/category/{cat_id}/todos', response_model=list[TodoResponse])
def get_cat_todos(db:SessionDep, user:AuthDep, cat_id:int):
    cat = db.exec(select(Category).where(Category.id==cat_id, Category.user_id==user.id)).one_or_none()
    return cat.todos