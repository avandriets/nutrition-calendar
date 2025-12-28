import { Module } from '@nestjs/common';
import { FoodLogController } from './food-log.controller';
import { FoodLogService } from './food-log.service';

@Module({
  controllers: [FoodLogController],
  providers: [FoodLogService]
})
export class FoodLogModule {
}
