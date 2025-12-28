export interface Account {
  accountId: string;
  name: string;
  createdAt: string;
  country?: string;
  timezone?: string;
  plan?: string;
  userIds?: string[];
}

export interface CreateAccountDto {
  accountId: string;
  name: string;
  country?: string;
  timezone?: string;
}
