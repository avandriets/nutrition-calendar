import { Module } from '@nestjs/common';
import { AccountsService } from './accounts.service';
import { AccountsController } from './accounts.controller';
import { DynamoModule } from '../dynamo/dynamo.module';
import { UsersModule } from '../users/users.module';

@Module({
  imports: [DynamoModule, UsersModule],
  providers: [AccountsService],
  controllers: [AccountsController],
  exports: [AccountsService],
})
export class AccountsModule {}
