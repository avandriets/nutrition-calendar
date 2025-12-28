import { Module } from '@nestjs/common';
import { DynamoModule } from './dynamo/dynamo.module';
import { FoodDictionaryModule } from './food-dictionary/food-dictionary.module';
import { ConfigModule } from '@nestjs/config';
import { AccountsModule } from './accounts/accounts.module';
import { UsersModule } from './users/users.module';
import { FoodLogModule } from './food-log/food-log.module';

@Module({
  imports: [DynamoModule, FoodDictionaryModule, ConfigModule.forRoot({ isGlobal: true }), AccountsModule, UsersModule, FoodLogModule],
})
export class AppModule {}
