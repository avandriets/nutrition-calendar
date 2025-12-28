import { Body, Controller, Delete, Get, Param, Patch, Post, Query } from '@nestjs/common';
import { FoodLogService } from './food-log.service';
import { CreateFoodLogRequestDto, DailyLogResponseDto, UpdateFoodLogRequestDto } from './dto';
import { FoodLogItem } from './interfaces';

@Controller('accounts/:accountId/users/:userId/food')
export class FoodLogController {
  constructor(private readonly foodLogService: FoodLogService) {}

  @Post()
  async addFoodItem(@Param('accountId') accountId: string, @Param('userId') userId: string, @Body() body: CreateFoodLogRequestDto): Promise<FoodLogItem> {
    return this.foodLogService.addItem({
      accountId,
      userId,
      date: body.date,
      mealType: body.mealType,
      productId: body.productId,
      amountGrams: body.amountGrams,
    });
  }

  @Get()
  async getDailyLog(@Param('accountId') accountId: string, @Param('userId') userId: string, @Query('date') date: string): Promise<DailyLogResponseDto> {
    // TODO Add check for empty data
    return this.foodLogService.getDailyLog(accountId, userId, date);
  }

  @Patch(':itemId')
  async updateFoodItem(@Param('accountId') accountId: string, @Param('itemId') itemId: string, @Body() body: UpdateFoodLogRequestDto): Promise<void> {
    await this.foodLogService.updateItem({
      accountId,
      itemId,
      amountGrams: body.amountGrams,
    });
  }

  @Delete(':itemId')
  async deleteFoodItem(@Param('accountId') accountId: string, @Param('itemId') itemId: string): Promise<void> {
    await this.foodLogService.deleteItem(accountId, itemId);
  }
}
