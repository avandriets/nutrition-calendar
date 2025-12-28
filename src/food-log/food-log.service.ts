import { Inject, Injectable } from '@nestjs/common';
import { DynamoDBDocumentClient, PutCommand, QueryCommand, UpdateCommand, DeleteCommand, BatchGetCommand } from '@aws-sdk/lib-dynamodb';
import { randomUUID } from 'node:crypto';
import { DYNAMO_DOCUMENT_CLIENT } from '../dynamo/dynamo.module';
import { CreateFoodLogDto, FoodLogItem, MealType, UpdateFoodLogDto } from './interfaces';
import { DailyAccountUsersLogResponseDto, DailyLogResponseDto, DailyMealGroupDto, DailyMealItemDto } from './dto';
import type { Product } from '../food-dictionary/interfaces';
import { TABLE_NAMES } from '../dynamo/dynamo.constants';

@Injectable()
export class FoodLogService {
  private FOOD_DICTIONARY = TABLE_NAMES.FOOD_DICTIONARY;
  private FOOD_LOG_TABLE = TABLE_NAMES.FOOD_LOG;
  private GSI1_NAME = TABLE_NAMES.GSI1_NAME;

  constructor(
    @Inject(DYNAMO_DOCUMENT_CLIENT)
    private readonly docClient: DynamoDBDocumentClient,
  ) {}

  private buildGsiPk(accountId: string, date: string, userId: string): string {
    return `${accountId}#${date}#${userId}`;
  }

  private buildGsiSk(mealType: MealType, createdAt: string): string {
    return `${mealType}#${createdAt}`;
  }

  async addItem(dto: CreateFoodLogDto): Promise<FoodLogItem> {
    const itemId = randomUUID();
    const createdAt = new Date().toISOString();

    const item: FoodLogItem & { gsi1pk: string; gsi1sk: string } = {
      accountId: dto.accountId,
      itemId,
      userId: dto.userId,
      date: dto.date,
      mealType: dto.mealType,
      productId: dto.productId,
      amountGrams: dto.amountGrams,
      createdAt,
      gsi1pk: this.buildGsiPk(dto.accountId, dto.date, dto.userId),
      gsi1sk: this.buildGsiSk(dto.mealType, createdAt),
    };

    await this.docClient.send(
      new PutCommand({
        TableName: this.FOOD_LOG_TABLE,
        Item: item,
      }),
    );

    return item;
  }

  async getDailyLog(accountId: string, userId: string, date: string): Promise<DailyLogResponseDto> {
    const gsiPk = this.buildGsiPk(accountId, date, userId);

    const res = await this.docClient.send(
      new QueryCommand({
        TableName: this.FOOD_LOG_TABLE,
        IndexName: this.GSI1_NAME,
        KeyConditionExpression: 'gsi1pk = :pk',
        ExpressionAttributeValues: {
          ':pk': gsiPk,
        },
      }),
    );

    const items = (res.Items || []) as FoodLogItem[];

    if (!items.length) {
      return {
        accountId,
        userId,
        date,
        totalCalories: 0,
        totalProtein: 0,
        totalFat: 0,
        totalCarbs: 0,
        meals: [],
      };
    }

    const uniqueProductIds = Array.from(new Set(items.map((i) => i.productId)));

    const batchRes = await this.docClient.send(
      new BatchGetCommand({
        RequestItems: {
          [this.FOOD_DICTIONARY]: {
            Keys: uniqueProductIds.map((productId) => ({ foodId: productId })),
          },
        },
      }),
    );

    const productsRaw = batchRes.Responses?.[this.FOOD_DICTIONARY] || [];
    const productsMap = new Map<string, Product>();

    for (const p of productsRaw as Product[]) {
      productsMap.set(p.foodId, p);
    }

    const mealsMap = new Map<string, DailyMealGroupDto>();

    for (const item of items) {
      const product = productsMap.get(item.productId);
      if (!product) {
        continue;
      }

      const factor = item.amountGrams / 100;

      const calories = product.caloriesPer100g * factor;
      const protein = product.proteinPer100g * factor;
      const fat = product.fatPer100g * factor;
      const carbs = product.carbsPer100g * factor;

      if (!mealsMap.has(item.mealType)) {
        mealsMap.set(item.mealType, {
          mealType: item.mealType,
          totalCalories: 0,
          totalProtein: 0,
          totalFat: 0,
          totalCarbs: 0,
          items: [],
        });
      }

      const group = mealsMap.get(item.mealType)!;

      const mealItem: DailyMealItemDto = {
        itemId: item.itemId,
        productId: item.productId,
        amountGrams: item.amountGrams,
        calories,
        protein,
        fat,
        carbs,
      };

      group.items.push(mealItem);
      group.totalCalories += calories;
      group.totalProtein += protein;
      group.totalFat += fat;
      group.totalCarbs += carbs;
    }

    const meals = Array.from(mealsMap.values());

    const total = meals.reduce(
      (acc, m) => ({
        calories: acc.calories + m.totalCalories,
        protein: acc.protein + m.totalProtein,
        fat: acc.fat + m.totalFat,
        carbs: acc.carbs + m.totalCarbs,
      }),
      { calories: 0, protein: 0, fat: 0, carbs: 0 },
    );

    return {
      accountId,
      userId,
      date,
      totalCalories: total.calories,
      totalProtein: total.protein,
      totalFat: total.fat,
      totalCarbs: total.carbs,
      meals,
    };
  }

  async updateItem(dto: UpdateFoodLogDto): Promise<void> {
    const updateExpressions: string[] = [];
    const exprValues: Record<string, any> = {};

    if (dto.amountGrams !== undefined) {
      updateExpressions.push('amountGrams = :amount');
      exprValues[':amount'] = dto.amountGrams;
    }

    if (!updateExpressions.length) {
      return;
    }

    await this.docClient.send(
      new UpdateCommand({
        TableName: this.FOOD_LOG_TABLE,
        Key: {
          accountId: dto.accountId,
          itemId: dto.itemId,
        },
        UpdateExpression: 'SET ' + updateExpressions.join(', '),
        ExpressionAttributeValues: exprValues,
        ConditionExpression: 'attribute_exists(accountId) AND attribute_exists(itemId)',
      }),
    );
  }

  async deleteItem(accountId: string, itemId: string): Promise<void> {
    await this.docClient.send(
      new DeleteCommand({
        TableName: this.FOOD_LOG_TABLE,
        Key: { accountId, itemId },
        ConditionExpression: 'attribute_exists(accountId) AND attribute_exists(itemId)',
      }),
    );
  }

  async getDailyLogForAllUsers(accountId: string, date: string, userIds: string[]): Promise<DailyAccountUsersLogResponseDto> {
    if (!userIds.length) {
      return {
        accountId,
        date,
        users: {},
      };
    }

    const logs: DailyLogResponseDto[] = await Promise.all(userIds.map((userId) => this.getDailyLog(accountId, userId, date)));

    const users: DailyAccountUsersLogResponseDto['users'] = {};

    for (const log of logs) {
      if (log.meals.length) {
        users[log.userId] = {
          totalCalories: log.totalCalories,
          totalProtein: log.totalProtein,
          totalFat: log.totalFat,
          totalCarbs: log.totalCarbs,
          meals: log.meals,
        };
      }
    }

    return {
      accountId,
      date,
      users,
    };
  }
}
