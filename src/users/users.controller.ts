import { Body, Controller, Get, Param, Patch, Post } from '@nestjs/common';
import { UsersService } from './users.service';
import { randomUUID } from 'node:crypto';
import { User } from './interfaces';
import { CreateUserRequestDto } from './dto';

@Controller('accounts/:accountId/users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  async createUser(@Param('accountId') accountId: string, @Body() body: CreateUserRequestDto): Promise<User> {
    return this.usersService.createUser({
      accountId,
      userId: randomUUID(),
      name: body.name,
      role: body.role,
      targetCalories: body.targetCalories,
      targetProtein: body.targetProtein,
    });
  }

  @Patch(':userId/deactivate')
  async deactivateUser(@Param('accountId') accountId: string, @Param('userId') userId: string): Promise<void> {
    await this.usersService.deactivateUser(accountId, userId);
  }

  @Get(':userId')
  async getUser(@Param('accountId') accountId: string, @Param('userId') userId: string): Promise<User | null> {
    return this.usersService.getUserById(accountId, userId);
  }
}
