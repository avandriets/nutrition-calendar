import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';

export const DYNAMO_DOCUMENT_CLIENT = 'DYNAMO_DOCUMENT_CLIENT';

@Module({
  imports: [ConfigModule],
  providers: [
    {
      provide: DYNAMO_DOCUMENT_CLIENT,
      inject: [ConfigService],
      useFactory: (config: ConfigService) => {
        const client = new DynamoDBClient({
          region: config.get<string>('AWS_REGION'),
          endpoint: config.get<string>('DYNAMO_ENDPOINT') || undefined,
        });

        return DynamoDBDocumentClient.from(client, {
          marshallOptions: { removeUndefinedValues: true },
        });
      },
    },
  ],
  exports: [DYNAMO_DOCUMENT_CLIENT],
})
export class DynamoModule {}
