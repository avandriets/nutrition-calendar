from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.users.model import AccountUser, BodyMeasurement, UserGoal


class DuplicateDatedRecordError(Exception):
    """Raised when a user already has the same record date."""


def commit(db: Session, entity):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateDatedRecordError from exc
    db.refresh(entity)
    return entity


def create_user(db: Session, account_id: int, data: Dict[str, Any]) -> AccountUser:
    user = AccountUser(account_id=account_id, **data)
    db.add(user)
    return commit(db, user)


def list_users(db: Session, account_id: int) -> List[AccountUser]:
    return db.query(AccountUser).filter(AccountUser.account_id == account_id).order_by(AccountUser.id).all()


def get_user(db: Session, account_id: int, user_id: int) -> Optional[AccountUser]:
    return db.query(AccountUser).filter(AccountUser.account_id == account_id, AccountUser.id == user_id).first()


def update_user(db: Session, user: AccountUser, data: Dict[str, Any]) -> AccountUser:
    for field, value in data.items():
        setattr(user, field, value)
    return commit(db, user)


def delete_entity(db: Session, entity) -> None:
    db.delete(entity)
    db.commit()


def create_goal(db: Session, user_id: int, data: Dict[str, Any]) -> UserGoal:
    goal = UserGoal(user_id=user_id, **data)
    db.add(goal)
    return commit(db, goal)


def list_goals(db: Session, user_id: int) -> List[UserGoal]:
    return db.query(UserGoal).filter(UserGoal.user_id == user_id).order_by(UserGoal.effective_from.desc(), UserGoal.id.desc()).all()


def get_goal(db: Session, user_id: int, goal_id: int) -> Optional[UserGoal]:
    return db.query(UserGoal).filter(UserGoal.user_id == user_id, UserGoal.id == goal_id).first()


def get_current_goal(db: Session, user_id: int) -> Optional[UserGoal]:
    return db.query(UserGoal).filter(UserGoal.user_id == user_id, UserGoal.effective_from <= date.today()).order_by(UserGoal.effective_from.desc(), UserGoal.id.desc()).first()


def get_goal_timeline(
    db: Session,
    user_id: int,
    date_from: date,
    date_to: date,
) -> List[Dict[str, Any]]:
    goals = (
        db.query(UserGoal)
        .filter(UserGoal.user_id == user_id, UserGoal.effective_from <= date_to)
        .order_by(UserGoal.effective_from, UserGoal.id)
        .all()
    )
    periods = []
    for index, goal in enumerate(goals):
        next_date = goals[index + 1].effective_from if index + 1 < len(goals) else None
        period_start = max(goal.effective_from, date_from)
        period_end = min(next_date - date.resolution, date_to) if next_date else date_to
        if period_start > period_end:
            continue
        periods.append({
            "goal_id": goal.id,
            "daily_calories_kcal": goal.daily_calories_kcal,
            "daily_protein_g": goal.daily_protein_g,
            "daily_fiber_g": goal.daily_fiber_g,
            "effective_from": goal.effective_from,
            "period_start": period_start,
            "period_end": period_end,
        })
    return periods


def update_goal(db: Session, goal: UserGoal, data: Dict[str, Any]) -> UserGoal:
    for field, value in data.items():
        setattr(goal, field, value)
    return commit(db, goal)


def create_measurement(db: Session, user_id: int, data: Dict[str, Any]) -> BodyMeasurement:
    measurement = BodyMeasurement(user_id=user_id, **data)
    db.add(measurement)
    return commit(db, measurement)


def list_measurements(db: Session, user_id: int) -> List[BodyMeasurement]:
    return db.query(BodyMeasurement).filter(BodyMeasurement.user_id == user_id).order_by(BodyMeasurement.measured_on.desc(), BodyMeasurement.id.desc()).all()


def get_measurement(db: Session, user_id: int, measurement_id: int) -> Optional[BodyMeasurement]:
    return db.query(BodyMeasurement).filter(BodyMeasurement.user_id == user_id, BodyMeasurement.id == measurement_id).first()


def update_measurement(db: Session, measurement: BodyMeasurement, data: Dict[str, Any]) -> BodyMeasurement:
    for field, value in data.items():
        setattr(measurement, field, value)
    return commit(db, measurement)
