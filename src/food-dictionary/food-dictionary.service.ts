import { BadRequestException, Inject, Injectable } from '@nestjs/common';
import { DynamoDBDocumentClient, PutCommand, GetCommand, ScanCommand, UpdateCommand, DeleteCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';
import { randomUUID } from 'node:crypto';
import { DYNAMO_DOCUMENT_CLIENT } from '../dynamo/dynamo.module';

import type { Product } from './interfaces';
import { CreateFoodDto, UpdateFoodDto } from './dto';
import { TABLE_NAMES } from '../dynamo/dynamo.constants';

@Injectable()
export class FoodDictionaryService {
  private FOOD_DICTIONARY = TABLE_NAMES.FOOD_DICTIONARY;
  private FOOD_LOG_TABLE = TABLE_NAMES.FOOD_LOG;
  private FOOD_LOG_FOOD_INDEX = TABLE_NAMES.FOOD_LOG_FOOD_INDEX;

  constructor(
    @Inject(DYNAMO_DOCUMENT_CLIENT)
    private readonly dynamo: DynamoDBDocumentClient,
  ) {}

  async create(data: CreateFoodDto): Promise<Product> {
    const foodId = randomUUID();

    const item: Product = {
      foodId,
      ...data,
    };

    await this.dynamo.send(
      new PutCommand({
        TableName: this.FOOD_DICTIONARY,
        Item: item,
        ConditionExpression: 'attribute_not_exists(foodId)',
      }),
    );

    return item;
  }

  async findAll(): Promise<Product[]> {
    const result = await this.dynamo.send(
      new ScanCommand({
        TableName: this.FOOD_DICTIONARY,
      }),
    );

    return (result.Items as Product[]) ?? [];
  }

  async findOne(foodId: string): Promise<Product | null> {
    const result = await this.dynamo.send(
      new GetCommand({
        TableName: this.FOOD_DICTIONARY,
        Key: { foodId },
      }),
    );

    return (result.Item as Product) ?? null;
  }

  async update(foodId: string, data: UpdateFoodDto): Promise<Product | null> {
    const updateExpr: string[] = [];
    const exprValues: Record<string, unknown> = {};
    const exprNames: Record<string, string> = {};

    for (const [key, value] of Object.entries(data)) {
      if (value === undefined) {
        continue;
      }

      const attrName = `#${key}`;
      const attrValue = `:${key}`;

      updateExpr.push(`${attrName} = ${attrValue}`);
      exprNames[attrName] = key;
      exprValues[attrValue] = value;
    }

    if (!updateExpr.length) {
      return this.findOne(foodId);
    }

    await this.dynamo.send(
      new UpdateCommand({
        TableName: this.FOOD_DICTIONARY,
        Key: { foodId },
        UpdateExpression: `SET ${updateExpr.join(', ')}`,
        ExpressionAttributeNames: exprNames,
        ExpressionAttributeValues: exprValues,
        ConditionExpression: 'attribute_exists(foodId)',
      }),
    );

    return this.findOne(foodId);
  }

  async remove(foodId: string) {
    const usage = await this.dynamo.send(
      new QueryCommand({
        TableName: this.FOOD_LOG_TABLE,
        IndexName: this.FOOD_LOG_FOOD_INDEX,
        KeyConditionExpression: 'foodId = :fid',
        ExpressionAttributeValues: {
          ':fid': foodId,
        },
        Limit: 1,
      }),
    );

    if (usage.Count && usage.Count > 0) {
      throw new BadRequestException('Нельзя удалить продукт: он уже используется в дневнике питания.');
    }

    await this.dynamo.send(
      new DeleteCommand({
        TableName: this.FOOD_DICTIONARY,
        Key: { foodId },
        ConditionExpression: 'attribute_exists(foodId)',
      }),
    );

    return { success: true };
  }
}
