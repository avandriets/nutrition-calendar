import { Module } from '@nestjs/common';
import { FoodLogController } from './food-log.controller';
import { FoodLogService } from './food-log.service';
import { DynamoModule } from '../dynamo/dynamo.module';
import { AccountsModule } from '../accounts/accounts.module';
import { FoodLogAccountController } from './food-log-account.controller';

@Module({
  imports: [DynamoModule, AccountsModule],
  controllers: [FoodLogController, FoodLogAccountController],
  providers: [FoodLogService],
})
export class FoodLogModule {}
