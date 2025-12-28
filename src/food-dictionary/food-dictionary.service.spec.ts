import { Test, TestingModule } from '@nestjs/testing';
import { FoodDictionaryService } from './food-dictionary.service';

describe('FoodDictionaryService', () => {
  let service: FoodDictionaryService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [FoodDictionaryService],
    }).compile();

    service = module.get<FoodDictionaryService>(FoodDictionaryService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});
