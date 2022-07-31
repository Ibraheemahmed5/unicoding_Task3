from ninja import Router
from ninja.security import django_auth
from django.shortcuts import get_object_or_404
from accounting.models import Account, AccountTypeChoices
from accounting.schemas import AccountOut, FourOFourOut, GeneralLedgerOut
from typing import List
from django.db.models import Sum, Avg
from rest_framework import status

from restauth.authorization import AuthBearer

account_router = Router(tags=['account'])


@account_router.get("/get_all", response=List[AccountOut])
def get_all(request):
    return status.HTTP_200_OK, Account.objects.order_by('full_code')


@account_router.get('/get_one/{account_id}/', response={
    200: AccountOut,
    404: FourOFourOut,
})
def get_one(request, account_id: int):
    try:
        account = Account.objects.get(id=account_id)
        return account
    except Account.DoesNotExist:
        return 404, {'detail': f'Account with id {account_id} does not exist'}


@account_router.get('/get_account_types/')
def get_account_types(request):
    return {t[0]: t[1] for t in AccountTypeChoices.choices}


@account_router.get('/account-balance/{account_id}', response=GeneralLedgerOut)
def get_account_balance(request, account_id: int):
    account = get_object_or_404(Account, id=account_id)

    balance = account.balance()

    journal_entries = account.journal_entries.all()

    return 200, {'account': account.name, 'balance': list(balance), 'jes': list(journal_entries)}


@account_router.get('/account-balances/', response=List[GeneralLedgerOut])
def get_account_balances(request):
    accounts = Account.objects.all()
    result = []
    for a in accounts:
        result.append({
            'account': a.name, 'balance': list(a.balance())
        })

    return status.HTTP_200_OK, result


@account_router.get('/Account-Balances-Total/', response=List[GeneralLedgerOut])
def get_account_balances(request):
    accounts = Account.objects.all().filter(parent=None)

    result = []
    for a in accounts.all():
        total = None
        main_balance = Balance(a.balance())

        children = a.children.all()

        for child in children:
            balance_object = Balance(child.balance())

            total = main_balance.__add__(balance_object)
        result.append({
            'account': a.name, 'balance': list(total)
        })

    return 200, result


class Balance:

    def __init__(self, balances):
        balanceIQD = 0
        balanceUSD = 0
        for i in balances:
            if i['currency'] == 'USD':
                balanceUSD = i['sum']
            if i['currency'] == 'IQD':
                balanceIQD = i['sum']

        # if balance1['currency'] == 'USD':
        #     balanceUSD = balance1['sum']
        #     balanceIQD = balance2['sum']
        # else:
        #     balanceIQD = balance1['sum']
        #     balanceUSD = balance2['sum']

        self.balanceUSD = balanceUSD
        self.balanceIQD = balanceIQD
        
        if self.balanceUSD == 0 :
            self.balanceUSD = 0
            
        if self.balanceIQD == 0 :
            self.balanceIQD = 0
        
        

    def __add__(self, other):
        self.balanceIQD += other.balanceIQD
        self.balanceUSD += other.balanceUSD
        
        
            
        
        
        
        return [{
            'currency': 'USD',
            'sum': self.balanceUSD
        }, {
            'currency': 'IQD',
            'sum': self.balanceIQD
        }]
