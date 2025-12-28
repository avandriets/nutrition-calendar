import { DailyMealGroupDto } from './daily-log-response.dto';

export class DailyAccountUsersLogResponseDto {
  accountId: string;
  date: string;
  users: {
    [userId: string]: {
      totalCalories: number;
      totalProtein: number;
      totalFat: number;
      totalCarbs: number;
      meals: DailyMealGroupDto[];
    };
  };
}
