import secrets

from typing import List

from pagermaid.enums import Message
from pagermaid.listener import listener

games = {}


class Game:
    password: List[int]
    times: int

    def __init__(self):
        self.times = 0
        self.gen_password()

    def gen_password(self):
        ans = []
        while len(ans) != 4:
            n = secrets.choice(range(10))
            if n not in ans:
                ans.append(n)
        self.password = ans

    @staticmethod
    def check_input(answer: str):
        numbers = " ".join(answer).split()
        if len(numbers) != 4:
            return False
        data = [0, 0, 0, 0]
        for i in range(4):
            data[i] = int(numbers[i])
        return data

    def check_answer(self, answer: str):
        nums = self.check_input(answer)
        if not nums:
            raise ValueError("Invalid input")
        a, b = 0, 0
        for n in nums:
            if n in self.password:
                if nums.index(n) == self.password.index(n):
                    a += 1
                else:
                    b += 1
        self.times += 1
        return a, b


@listener(command="1A2B",
          groups_only=True,
          description="Play a game of 1A2B",
          parameters="<start/stop/answer>")
async def play_game_1a2b(message: Message):
    if not message.arguments:
        return await message.edit("Please specify a command.")
    game = games.get(message.chat.id, None)
    if message.arguments == "start":
        if game:
            return await message.edit("Game already started.")
        games[message.chat.id] = Game()
        return await message.edit("Game started.")
    if message.arguments == "stop":
        if not game:
            return await message.edit("Game not started.")
        del games[message.chat.id]
        return await message.edit("Game stopped.")
    if message.arguments == "answer":
        if not game:
            return await message.edit("Game not started.")
        answer = "".join(map(str, game.password))
        return await message.edit(f"The answer is: {answer}\n\nGame over.")
    if game:
        try:
            a, b = game.check_answer(message.arguments)
        except ValueError:
            return await message.edit("You need to guess 4 numbers between 0 ~ 9.\nFor example: 1234")
        if a == 4:
            return await message.edit("You Win!\n\nGame over.")
        return await message.edit("%d:  %dA%dB" % (game.times, a, b))
