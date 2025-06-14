import asyncio
import grpc
import generated.game_pb2 as game_pb2
import generated.game_pb2_grpc as game_pb2_grpc
import random

async def simulate_player(name, game_id=None):
    async with grpc.aio.insecure_channel("localhost:50055") as channel:
        stub = game_pb2_grpc.GameServiceStub(channel)

        # Join game
        join_request = game_pb2.JoinRequest(player_name=name, game_id=game_id or "")
        join_response = await stub.JoinGame(join_request)

        player_id = join_response.player_id
        assigned_game_id = join_response.game_id
        print(f"[{name}] Joined game {assigned_game_id} with ID {player_id}")

        # Start listening to leaderboard updates
        async def stream_leaderboard():
            async for update in stub.StreamLeaderboard(game_pb2.GameId(game_id=assigned_game_id)):
                print(f"[{name}] Leaderboard Update:")
                for entry in update.leaderboard.entries:
                    print(f"  {entry.player_name} - Score: {entry.score}")
                if update.game_over:
                    print(f"[{name}] Game Over! Final Scores above 👆")
                    break


        # Start the game to receive questions
        async def play_game():
            question_stream = stub.StartGame(
                game_pb2.GameRequest(game_id=assigned_game_id, player_id=player_id)
            )
            async for question in question_stream:
                print(f"[{name}] Q: {question.question_text} | Options: {question.options}")
                answer = random.choice(question.options)  # pick first option
                await asyncio.sleep(1)  # simulate thinking time

                result = await stub.SubmitAnswer(
                    game_pb2.AnswerRequest(
                        game_id=assigned_game_id,
                        player_id=player_id,
                        question_id=question.question_id,
                        selected_option=answer,
                        answer_timestamp=int(asyncio.get_event_loop().time())
                    )
                )
                print(f"[{name}] Answered {answer}: {'Correct' if result.correct else 'Wrong'} | Points: {result.points_awarded}")

        await asyncio.gather(
            stream_leaderboard(),
            play_game()
        )


async def run():
    game_id = None  # leave this as None to create a new game, then reuse it
    await asyncio.gather(
        simulate_player("Vinayak", game_id),
        simulate_player("Rohit", game_id)
    )

if __name__ == "__main__":
    asyncio.run(run())
