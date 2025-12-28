import { Controller, Get, Post, Body, Param, Delete, Patch } from '@nestjs/common';
import { FoodDictionaryService } from './food-dictionary.service';

import { CreateFoodDto, UpdateFoodDto, CreateFoodRequestDto, UpdateFoodRequestDto } from './dto';

@Controller('food')
export class FoodDictionaryController {
  constructor(private readonly service: FoodDictionaryService) {}

  @Post()
  create(@Body() body: CreateFoodRequestDto) {
    const dto: CreateFoodDto = {
      name: body.name,
      caloriesPer100g: body.caloriesPer100g,
      proteinPer100g: body.proteinPer100g,
      carbsPer100g: body.carbsPer100g,
      fatPer100g: body.fatPer100g,
    };

    return this.service.create(dto);
  }

  @Get()
  findAll() {
    return this.service.findAll();
  }

  @Get(':foodId')
  findOne(@Param('foodId') foodId: string) {
    return this.service.findOne(foodId);
  }

  @Patch(':foodId')
  update(@Param('foodId') foodId: string, @Body() body: UpdateFoodRequestDto) {
    const dto: UpdateFoodDto = {
      name: body.name,
      caloriesPer100g: body.caloriesPer100g,
      proteinPer100g: body.proteinPer100g,
      carbsPer100g: body.carbsPer100g,
      fatPer100g: body.fatPer100g,
    };

    return this.service.update(foodId, dto);
  }

  @Delete(':foodId')
  remove(@Param('foodId') foodId: string) {
    return this.service.remove(foodId);
  }
}
