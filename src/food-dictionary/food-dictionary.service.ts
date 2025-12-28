import { Inject, Injectable } from '@nestjs/common';
import {
  DynamoDBDocumentClient,
  PutCommand,
  GetCommand,
  ScanCommand,
  UpdateCommand,
  DeleteCommand
} from '@aws-sdk/lib-dynamodb';
import { randomUUID } from 'node:crypto';
import { DYNAMO_DOCUMENT_CLIENT } from '../dynamo/dynamo.module';

import type { Product } from './interfaces';
import { CreateFoodDto, UpdateFoodDto } from './dto';
import { TABLE_NAMES } from '../dynamo/dynamo.constants';

@Injectable()
export class FoodDictionaryService {
  private FOOD_DICTIONARY = TABLE_NAMES.FOOD_DICTIONARY;

  constructor(
    @Inject(DYNAMO_DOCUMENT_CLIENT)
    private readonly dynamo: DynamoDBDocumentClient,
  ) {
  }

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

    for (const key of Object.keys(data)) {
      updateExpr.push(`${key} = :${key}`);
      exprValues[`:${key}`] = (data as any)[key];
    }

    await this.dynamo.send(
      new UpdateCommand({
        TableName: this.FOOD_DICTIONARY,
        Key: { foodId },
        UpdateExpression: `SET ${updateExpr.join(', ')}`,
        ExpressionAttributeValues: exprValues,
        ConditionExpression: 'attribute_exists(foodId)',
      }),
    );

    return this.findOne(foodId);
  }

  async remove(foodId: string) {
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
