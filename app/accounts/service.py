from typing import List, Optional

from sqlalchemy.orm import Session

from app.accounts.model import Account
from app.accounts.schemas import AccountCreate, AccountUpdate


def create_account(db: Session, payload: AccountCreate) -> Account:
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_accounts(db: Session, skip: int, limit: int) -> List[Account]:
    return db.query(Account).order_by(Account.id).offset(skip).limit(limit).all()


def get_account(db: Session, account_id: int) -> Optional[Account]:
    return db.query(Account).filter(Account.id == account_id).first()


def update_account(db: Session, account: Account, payload: AccountUpdate) -> Account:
    for field, value in payload.model_dump().items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, account: Account) -> None:
    db.delete(account)
    db.commit()
