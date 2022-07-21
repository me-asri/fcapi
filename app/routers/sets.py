from typing import List

from fastapi import APIRouter, Depends, Body, Response, status

from app.tags import Tags
from app.models import Result, UserDb, Card, Set, SetDb
from app.sql.database import Session
from app.dependencies import get_db
from app.routers.users import get_active_current_user

from app.sql.crud import set as set_crud

router = APIRouter(
    prefix='/sets',
    tags=[Tags.sets]
)


@router.post(
    '/',
    response_model=Result,
    summary='Create/update a set for user'
)
def create_set(response: Response,
               set: Set = Body(description='Set description'),
               user: UserDb = Depends(get_active_current_user),
               db: Session = Depends(get_db)):
    """
    Creates or updates (if ID exists) a set
    """

    set = set_crud.add_set(db, set, user)
    if not set:
        return Result(code=status.HTTP_400_BAD_REQUEST, message='Failed to add set')

    return Result(code=status.HTTP_200_OK, message='Operation successful')


@router.get(
    '/',
    response_model=List[Set],
    summary='Get sets owned by user'
)
def get_sets(user: UserDb = Depends(get_active_current_user), db: Session = Depends(get_db)):
    """
    Returns all sets owned by the user
    """

    return set_crud.get_sets(db, user)


@router.get(
    '/{id}',
    response_model=Set,
    summary="Get set by ID"
)
def get_set(id: int, user: UserDb = Depends(get_active_current_user), db: Session = Depends(get_db)):
    """
    Returns a set matching given ID owned by the user
    """

    return set_crud.get_set(db, user, id)


@router.delete(
    '/{id}',
    response_model=Result,
    summary="Remove a set"
)
def delete_set(
        id: int,
        response: Response,
        user: UserDb = Depends(get_active_current_user),
        db: Session = Depends(get_db)
):
    """
    Removes a set matching given ID owned by the user
    """
    if set_crud.del_set(db, user, id):
        return Result(code=status.HTTP_200_OK, message='Set deleted successfully')
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Result(code=status.HTTP_400_BAD_REQUEST, message='Failed to delete set')
