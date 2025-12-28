import { IsNumber, IsOptional } from 'class-validator';

export class UpdateFoodLogRequestDto {
  @IsOptional()
  @IsNumber()
  amountGrams?: number;
}
