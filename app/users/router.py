from datetime import date
from typing import List, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.accounts.router import get_account_or_404
from app.database import get_db
from app.users import service
from app.users.model import AccountUser, BodyMeasurement, UserGoal
from app.users.schemas import (
    GoalCreate, GoalResponse, GoalTimelineResponse, GoalUpdate,
    MeasurementCreate, MeasurementResponse, MeasurementUpdate,
    UserCreate, UserResponse, UserUpdate,
)

router = APIRouter(prefix="/accounts/{account_id}/users", tags=["account users"])


def get_user_or_404(account_id: int, user_id: int, db: Session) -> AccountUser:
    get_account_or_404(account_id, db)
    user = service.get_user(db, account_id, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_goal_or_404(user_id: int, goal_id: int, db: Session) -> UserGoal:
    goal = service.get_goal(db, user_id, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


def get_measurement_or_404(user_id: int, measurement_id: int, db: Session) -> BodyMeasurement:
    measurement = service.get_measurement(db, user_id, measurement_id)
    if measurement is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return measurement


def raise_date_conflict(detail: str) -> NoReturn:
    raise HTTPException(status_code=409, detail=detail)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(account_id: int, payload: UserCreate, db: Session = Depends(get_db)) -> AccountUser:
    get_account_or_404(account_id, db)
    return service.create_user(db, account_id, payload.model_dump())


@router.get("", response_model=List[UserResponse])
def list_users(account_id: int, db: Session = Depends(get_db)) -> List[AccountUser]:
    get_account_or_404(account_id, db)
    return service.list_users(db, account_id)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(account_id: int, user_id: int, db: Session = Depends(get_db)) -> AccountUser:
    return get_user_or_404(account_id, user_id, db)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(account_id: int, user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> AccountUser:
    user = get_user_or_404(account_id, user_id, db)
    return service.update_user(db, user, payload.model_dump())


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(account_id: int, user_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_entity(db, get_user_or_404(account_id, user_id, db))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{user_id}/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(account_id: int, user_id: int, payload: GoalCreate, db: Session = Depends(get_db)) -> UserGoal:
    user = get_user_or_404(account_id, user_id, db)
    try:
        return service.create_goal(db, user.id, payload.model_dump())
    except service.DuplicateDatedRecordError:
        raise_date_conflict("A goal already exists for this effective date")


@router.get("/{user_id}/goals", response_model=List[GoalResponse])
def list_goals(account_id: int, user_id: int, db: Session = Depends(get_db)) -> List[UserGoal]:
    user = get_user_or_404(account_id, user_id, db)
    return service.list_goals(db, user.id)


@router.get("/{user_id}/goals/current", response_model=GoalResponse)
def get_current_goal(account_id: int, user_id: int, db: Session = Depends(get_db)) -> UserGoal:
    user = get_user_or_404(account_id, user_id, db)
    goal = service.get_current_goal(db, user.id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Current goal not found")
    return goal


@router.get("/{user_id}/goals/timeline", response_model=GoalTimelineResponse)
def get_goal_timeline(
    account_id: int,
    user_id: int,
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db),
) -> GoalTimelineResponse:
    if date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not be after date_to")
    user = get_user_or_404(account_id, user_id, db)
    return GoalTimelineResponse(
        user_id=user.id,
        date_from=date_from,
        date_to=date_to,
        periods=service.get_goal_timeline(db, user.id, date_from, date_to),
    )


@router.get("/{user_id}/goals/{goal_id}", response_model=GoalResponse)
def get_goal(account_id: int, user_id: int, goal_id: int, db: Session = Depends(get_db)) -> UserGoal:
    user = get_user_or_404(account_id, user_id, db)
    return get_goal_or_404(user.id, goal_id, db)


@router.put("/{user_id}/goals/{goal_id}", response_model=GoalResponse)
def update_goal(account_id: int, user_id: int, goal_id: int, payload: GoalUpdate, db: Session = Depends(get_db)) -> UserGoal:
    user = get_user_or_404(account_id, user_id, db)
    goal = get_goal_or_404(user.id, goal_id, db)
    try:
        return service.update_goal(db, goal, payload.model_dump())
    except service.DuplicateDatedRecordError:
        raise_date_conflict("A goal already exists for this effective date")


@router.delete("/{user_id}/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(account_id: int, user_id: int, goal_id: int, db: Session = Depends(get_db)) -> Response:
    user = get_user_or_404(account_id, user_id, db)
    service.delete_entity(db, get_goal_or_404(user.id, goal_id, db))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{user_id}/measurements", response_model=MeasurementResponse, status_code=status.HTTP_201_CREATED)
def create_measurement(account_id: int, user_id: int, payload: MeasurementCreate, db: Session = Depends(get_db)) -> BodyMeasurement:
    user = get_user_or_404(account_id, user_id, db)
    try:
        return service.create_measurement(db, user.id, payload.model_dump())
    except service.DuplicateDatedRecordError:
        raise_date_conflict("A measurement already exists for this date")


@router.get("/{user_id}/measurements", response_model=List[MeasurementResponse])
def list_measurements(account_id: int, user_id: int, db: Session = Depends(get_db)) -> List[BodyMeasurement]:
    user = get_user_or_404(account_id, user_id, db)
    return service.list_measurements(db, user.id)


@router.get("/{user_id}/measurements/{measurement_id}", response_model=MeasurementResponse)
def get_measurement(account_id: int, user_id: int, measurement_id: int, db: Session = Depends(get_db)) -> BodyMeasurement:
    user = get_user_or_404(account_id, user_id, db)
    return get_measurement_or_404(user.id, measurement_id, db)


@router.put("/{user_id}/measurements/{measurement_id}", response_model=MeasurementResponse)
def update_measurement(account_id: int, user_id: int, measurement_id: int, payload: MeasurementUpdate, db: Session = Depends(get_db)) -> BodyMeasurement:
    user = get_user_or_404(account_id, user_id, db)
    measurement = get_measurement_or_404(user.id, measurement_id, db)
    try:
        return service.update_measurement(db, measurement, payload.model_dump())
    except service.DuplicateDatedRecordError:
        raise_date_conflict("A measurement already exists for this date")


@router.delete("/{user_id}/measurements/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(account_id: int, user_id: int, measurement_id: int, db: Session = Depends(get_db)) -> Response:
    user = get_user_or_404(account_id, user_id, db)
    service.delete_entity(db, get_measurement_or_404(user.id, measurement_id, db))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
