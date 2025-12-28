import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { AccountsService } from './accounts.service';
import { UsersService } from '../users/users.service';
import { Account } from './interfaces';
import { User } from '../users/interfaces';
import { CreateAccountRequestDto } from './dto';

@Controller('accounts')
export class AccountsController {
  constructor(
    private readonly accountsService: AccountsService,
    private readonly usersService: UsersService,
  ) {}

  @Post()
  async createAccount(@Body() body: CreateAccountRequestDto): Promise<Account> {
    return await this.accountsService.createAccount({
      accountId: body.accountId,
      name: body.name,
      country: body.country,
      timezone: body.timezone,
    });
  }

  @Get(':accountId')
  async getAccount(@Param('accountId') accountId: string): Promise<Account | null> {
    return this.accountsService.getAccount(accountId);
  }

  @Get(':accountId/users')
  async getAccountUsers(@Param('accountId') accountId: string): Promise<User[]> {
    return this.usersService.getUsersByAccount(accountId);
  }
}
