export const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack'] as const;
export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack' | string;

export interface FoodLogItem {
  accountId: string;
  itemId: string;
  userId: string;
  date: string;
  mealType: MealType;
  productId: string;
  amountGrams: number;
  calories?: number;
  protein?: number;
  fat?: number;
  carbs?: number;
  createdAt: string;
}

export interface CreateFoodLogDto {
  accountId: string;
  userId: string;
  date: string;
  mealType: MealType;
  productId: string;
  amountGrams: number;
}

export interface UpdateFoodLogDto {
  accountId: string;
  itemId: string;
  amountGrams?: number;
}
