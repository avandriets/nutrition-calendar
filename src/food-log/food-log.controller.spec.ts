import { Test, TestingModule } from '@nestjs/testing';
import { FoodLogController } from './food-log.controller';

describe('FoodLogController', () => {
  let controller: FoodLogController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [FoodLogController],
    }).compile();

    controller = module.get<FoodLogController>(FoodLogController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});
