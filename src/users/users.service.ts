import { Inject, Injectable } from '@nestjs/common';
import { DynamoDBDocumentClient, QueryCommand, UpdateCommand, TransactWriteCommand, GetCommand } from '@aws-sdk/lib-dynamodb';
import { DYNAMO_DOCUMENT_CLIENT } from '../dynamo/dynamo.module';
import { CreateUserDto, User } from './interfaces';
import { TABLE_NAMES } from '../dynamo/dynamo.constants';

@Injectable()
export class UsersService {
  private USERS_TABLE = TABLE_NAMES.USERS;
  private ACCOUNTS_TABLE = TABLE_NAMES.ACCOUNTS;

  constructor(
    @Inject(DYNAMO_DOCUMENT_CLIENT)
    private readonly docClient: DynamoDBDocumentClient,
  ) {}

  async createUser(dto: CreateUserDto): Promise<User> {
    const user: User = {
      accountId: dto.accountId,
      userId: dto.userId,
      name: dto.name,
      role: dto.role ?? 'member',
      targetCalories: dto.targetCalories,
      targetProtein: dto.targetProtein,
      createdAt: new Date().toISOString(),
      isActive: true,
    };

    await this.docClient.send(
      new TransactWriteCommand({
        TransactItems: [
          {
            Put: {
              TableName: this.USERS_TABLE,
              Item: user,
              ConditionExpression: 'attribute_not_exists(accountId) AND attribute_not_exists(userId)',
            },
          },
          {
            Update: {
              TableName: this.ACCOUNTS_TABLE,
              Key: { accountId: dto.accountId },
              UpdateExpression: 'SET userIds = list_append(if_not_exists(userIds, :empty), :newUser)',
              ExpressionAttributeValues: {
                ':empty': [],
                ':newUser': [dto.userId],
              },
              ConditionExpression: 'attribute_exists(accountId)',
            },
          },
        ],
      }),
    );

    return user;
  }

  async getUsersByAccount(accountId: string): Promise<User[]> {
    const res = await this.docClient.send(
      new QueryCommand({
        TableName: this.USERS_TABLE,
        KeyConditionExpression: 'accountId = :acc',
        ExpressionAttributeValues: {
          ':acc': accountId,
        },
      }),
    );

    return (res.Items as User[]) ?? [];
  }

  async getUserById(accountId: string, userId: string): Promise<User | null> {
    const res = await this.docClient.send(
      new GetCommand({
        TableName: this.USERS_TABLE,
        Key: {
          accountId,
          userId,
        },
      }),
    );

    return (res.Item as User) ?? null;
  }

  async deactivateUser(accountId: string, userId: string): Promise<void> {
    await this.docClient.send(
      new UpdateCommand({
        TableName: this.USERS_TABLE,
        Key: { accountId, userId },
        UpdateExpression: 'SET isActive = :false',
        ExpressionAttributeValues: {
          ':false': false,
        },
        ConditionExpression: 'attribute_exists(accountId) AND attribute_exists(userId)',
      }),
    );
  }
}
