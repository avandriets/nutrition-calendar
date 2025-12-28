import { MealType } from '../interfaces';

export interface DailyMealItemDto {
  itemId: string;
  productId: string;
  amountGrams: number;
  calories?: number;
  protein?: number;
  fat?: number;
  carbs?: number;
}

export interface DailyMealGroupDto {
  mealType: MealType;
  totalCalories: number;
  totalProtein: number;
  totalFat: number;
  totalCarbs: number;
  items: DailyMealItemDto[];
}

export interface DailyLogResponseDto {
  accountId: string;
  userId: string;
  date: string;
  totalCalories: number;
  totalProtein: number;
  totalFat: number;
  totalCarbs: number;
  meals: DailyMealGroupDto[];
}
