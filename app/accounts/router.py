from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.accounts import service
from app.accounts.model import Account
from app.accounts.schemas import AccountCreate, AccountResponse, AccountUpdate
from app.database import get_db

router = APIRouter(prefix="/accounts", tags=["accounts"])


def get_account_or_404(account_id: int, db: Session) -> Account:
    account = service.get_account(db, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> Account:
    return service.create_account(db, payload)


@router.get("", response_model=List[AccountResponse])
def list_accounts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[Account]:
    return service.list_accounts(db, skip, limit)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)) -> Account:
    return get_account_or_404(account_id, db)


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)) -> Account:
    return service.update_account(db, get_account_or_404(account_id, db), payload)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_account(db, get_account_or_404(account_id, db))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
