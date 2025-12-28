import { Test, TestingModule } from '@nestjs/testing';
import { FoodDictionaryController } from './food-dictionary.controller';

describe('FoodDictionaryController', () => {
  let controller: FoodDictionaryController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [FoodDictionaryController],
    }).compile();

    controller = module.get<FoodDictionaryController>(FoodDictionaryController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});
