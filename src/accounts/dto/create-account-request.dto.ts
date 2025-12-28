import { IsOptional, IsString } from 'class-validator';

export class CreateAccountRequestDto {
  @IsString()
  accountId: string;

  @IsString()
  name: string;

  @IsOptional()
  @IsString()
  country?: string;

  @IsOptional()
  @IsString()
  timezone?: string;
}
