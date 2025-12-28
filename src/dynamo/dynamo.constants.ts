export const TABLE_NAMES = {
  ACCOUNTS: process.env.ACCOUNTS_TABLE ?? 'accounts',
  USERS: process.env.USERS_TABLE ?? 'users',
  FOOD_DICTIONARY: process.env.FOOD_DICTIONARY_TABLE ?? 'food_dictionary',
  FOOD_LOG: process.env.FOOD_LOG_TABLE ?? 'food_log',
} as const;
