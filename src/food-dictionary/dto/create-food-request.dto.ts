import { IsNumber, IsString } from 'class-validator';

export class CreateFoodRequestDto {
  @IsString()
  name: string;

  @IsNumber()
  caloriesPer100g: number;

  @IsNumber()
  proteinPer100g: number;

  @IsNumber()
  carbsPer100g: number;

  @IsNumber()
  fatPer100g: number;
}
