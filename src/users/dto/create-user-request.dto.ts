import { IsIn, IsNumber, IsOptional, IsString } from 'class-validator';

export class CreateUserRequestDto {
  @IsString()
  name: string;

  @IsOptional()
  @IsString()
  @IsIn(['owner', 'member'])
  role?: 'owner' | 'member';

  @IsOptional()
  @IsNumber()
  targetCalories?: number;

  @IsOptional()
  @IsNumber()
  targetProtein?: number;
}
