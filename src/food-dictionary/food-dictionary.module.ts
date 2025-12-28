import { Module } from '@nestjs/common';
import { FoodDictionaryController } from './food-dictionary.controller';
import { FoodDictionaryService } from './food-dictionary.service';
import { DynamoModule } from '../dynamo/dynamo.module';

@Module({
  imports: [DynamoModule],
  controllers: [FoodDictionaryController],
  providers: [FoodDictionaryService],
})
export class FoodDictionaryModule {}
