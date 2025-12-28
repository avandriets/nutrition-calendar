import { Test, TestingModule } from '@nestjs/testing';
import { FoodLogService } from './food-log.service';

describe('FoodLogService', () => {
  let service: FoodLogService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [FoodLogService],
    }).compile();

    service = module.get<FoodLogService>(FoodLogService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});
