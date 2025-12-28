import { IsNumber, IsOptional, IsString } from 'class-validator';

export class UpdateFoodRequestDto {
  @IsOptional()
  @IsString()
  name?: string;

  @IsOptional()
  @IsNumber()
  caloriesPer100g?: number;

  @IsOptional()
  @IsNumber()
  proteinPer100g?: number;

  @IsOptional()
  @IsNumber()
  carbsPer100g?: number;

  @IsOptional()
  @IsNumber()
  fatPer100g?: number;
}
