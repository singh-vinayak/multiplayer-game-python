import asyncio
import grpc
import random

from generated import game_pb2, game_pb2_grpc


async def run():
    # Connect to the gRPC server
    async with grpc.aio.insecure_channel("localhost:50055") as channel:
        stub = game_pb2_grpc.GameServiceStub(channel)

        # Step 1: Join Game
        join_response = await stub.JoinGame(game_pb2.JoinRequest(player_name="Vinayak"))
        print(f"Joined game: {join_response.game_id} as {join_response.player_id}")
        
        game_id = join_response.game_id
        player_id = join_response.player_id

        # Step 2: Start Game & receive questions
        print("\nStarting game & receiving questions...\n")
        question_stream = stub.StartGame(game_pb2.GameRequest(game_id=game_id, player_id=player_id))

        question = await question_stream.read()
        if question:
            print(f"Question: {question.question_text}")
            for idx, opt in enumerate(question.options):
                print(f"{idx+1}. {opt}")
            
            selected_option = random.choice(question.options)
            print(f"\nSelected Option: {selected_option}")

            # Step 3: Submit Answer
            answer_result = await stub.SubmitAnswer(
                game_pb2.AnswerRequest(
                    game_id=game_id,
                    player_id=player_id,
                    question_id=question.question_id,
                    selected_option=selected_option,
                    answer_timestamp=int(asyncio.get_event_loop().time())
                )
            )

            print(f"\nAnswer Submitted: {'Correct' if answer_result.correct else 'Incorrect'}")
            print(f"Points Awarded: {answer_result.points_awarded}")
            print(f"Explanation: {answer_result.explanation}")

        else:
            print("No question received.")

        # Step 4: Fetch Leaderboard Once
        leaderboard = await stub.GetLeaderboard(game_pb2.GameId(game_id=game_id))
        print("\nLeaderboard:")
        for entry in leaderboard.entries:
            print(f"{entry.rank}. {entry.player_name} - {entry.score} points")

        # Step 5: Stream Live Leaderboard Updates (for 5 seconds)
        print("\nStreaming leaderboard updates for 5 seconds...")
        leaderboard_stream = stub.StreamLeaderboard(game_pb2.GameId(game_id=game_id))

        try:
            async for update in leaderboard_stream:
                print("📊 Live Leaderboard Update:")
                for entry in update.leaderboard.entries:
                    print(f"{entry.rank}. {entry.player_name} - {entry.score}")
                await asyncio.sleep(5)
                break  # Stop after first update for testing
        except Exception as e:
            print(f"Leaderboard stream error: {e}")


if __name__ == "__main__":
    asyncio.run(run())
