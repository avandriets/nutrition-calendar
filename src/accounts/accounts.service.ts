import { Inject, Injectable } from '@nestjs/common';
import { DynamoDBDocumentClient, PutCommand, GetCommand, UpdateCommand } from '@aws-sdk/lib-dynamodb';
import { DYNAMO_DOCUMENT_CLIENT } from '../dynamo/dynamo.module';
import { Account, CreateAccountDto } from './interfaces';
import { TABLE_NAMES } from '../dynamo/dynamo.constants';

@Injectable()
export class AccountsService {
  private ACCOUNTS_TABLE = TABLE_NAMES.ACCOUNTS;

  constructor(
    @Inject(DYNAMO_DOCUMENT_CLIENT)
    private readonly docClient: DynamoDBDocumentClient,
  ) {}

  async createAccount(dto: CreateAccountDto): Promise<Account> {
    const account: Account = {
      accountId: dto.accountId,
      name: dto.name,
      createdAt: new Date().toISOString(),
      country: dto.country,
      timezone: dto.timezone,
      plan: 'free',
      userIds: [],
    };

    await this.docClient.send(
      new PutCommand({
        TableName: this.ACCOUNTS_TABLE,
        Item: account,
        ConditionExpression: 'attribute_not_exists(accountId)',
      }),
    );

    return account;
  }

  async getAccount(accountId: string): Promise<Account | null> {
    const res = await this.docClient.send(
      new GetCommand({
        TableName: this.ACCOUNTS_TABLE,
        Key: { accountId },
      }),
    );

    return (res.Item as Account) ?? null;
  }

  async addUserId(accountId: string, userId: string): Promise<void> {
    await this.docClient.send(
      new UpdateCommand({
        TableName: this.ACCOUNTS_TABLE,
        Key: { accountId },
        UpdateExpression: 'ADD userIds :u',
        ExpressionAttributeValues: {
          ':u': new Set([userId]),
        },
        ConditionExpression: 'attribute_exists(accountId)',
      }),
    );
  }

  async removeUserId(accountId: string, userId: string): Promise<void> {
    await this.docClient.send(
      new UpdateCommand({
        TableName: this.ACCOUNTS_TABLE,
        Key: { accountId },
        UpdateExpression: 'DELETE userIds :u',
        ExpressionAttributeValues: {
          ':u': new Set([userId]),
        },
        ConditionExpression: 'attribute_exists(accountId)',
      }),
    );
  }
}
