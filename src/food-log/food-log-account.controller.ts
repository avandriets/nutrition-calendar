import { Controller, Get, Param, Query } from '@nestjs/common';
import { FoodLogService } from './food-log.service';
import { AccountsService } from '../accounts/accounts.service';
import { DailyAccountUsersLogResponseDto } from './dto';

@Controller('accounts/:accountId/food')
export class FoodLogAccountController {
  constructor(
    private readonly foodLogService: FoodLogService,
    private readonly accountsService: AccountsService,
  ) {}

  @Get()
  async getDailyAccountLog(@Param('accountId') accountId: string, @Query('date') date: string): Promise<DailyAccountUsersLogResponseDto> {
    const account = await this.accountsService.getAccount(accountId);
    const userIds = account?.userIds ?? [];

    return this.foodLogService.getDailyLogForAllUsers(accountId, date, userIds);
  }
}
