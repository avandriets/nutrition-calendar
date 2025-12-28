export const TABLE_NAMES = {
  ACCOUNTS: process.env.ACCOUNTS_TABLE ?? 'Accounts',
  USERS: process.env.USERS_TABLE ?? 'Users',
  FOOD_DICTIONARY: process.env.FOOD_DICTIONARY_TABLE ?? 'food_dictionary',
  FOOD_LOG: process.env.FOOD_LOG_TABLE ?? 'FoodLog',
  FOOD_LOG_FOOD_INDEX: process.env.FOOD_LOG_FOOD_INDEX ?? 'GSI2_Food',
  GSI1_NAME: process.env.GSI1_NAME ?? 'GSI1_DailyLog',
} as const;
