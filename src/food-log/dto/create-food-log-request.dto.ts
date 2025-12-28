import { IsString, IsNumber, IsIn } from 'class-validator';
import { MEAL_TYPES } from '../interfaces';
import type { MealType } from '../interfaces';

export class CreateFoodLogRequestDto {
  @IsString()
  date: string;

  @IsString()
  @IsIn(MEAL_TYPES)
  mealType: MealType;

  @IsString()
  productId: string;

  @IsNumber()
  amountGrams: number;
}
