export interface User {
  accountId: string;
  userId: string;
  name: string;
  role: 'owner' | 'member';
  targetCalories?: number;
  targetProtein?: number;
  createdAt: string;
  isActive: boolean;
}

export interface CreateUserDto {
  accountId: string;
  userId: string;
  name: string;
  role?: 'owner' | 'member';
  targetCalories?: number;
  targetProtein?: number;
}
