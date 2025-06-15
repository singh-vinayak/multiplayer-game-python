import asyncio
import grpc
from generated import game_pb2, game_pb2_grpc

SERVER_ADDRESS = "localhost:50055"  # adjust if your server runs on a different port

async def run():
    async with grpc.aio.insecure_channel(SERVER_ADDRESS) as channel:
        stub = game_pb2_grpc.GameServiceStub(channel)

        # 1. Join game
        print("Joining game...")
        join_response = await stub.JoinGame(game_pb2.JoinRequest(player_name="Alice"))
        player_id = join_response.player_id
        game_id = join_response.game_id
        print(f"Joined game: {game_id} as player: {player_id}")

        # 2. Get first question
        print("Getting first question...")
        question_response = await stub.GetNextQuestion(
            game_pb2.GameRequest(game_id=game_id, player_id=player_id)
        )

        if not question_response.question_id:
            print("No question received (possibly waiting for more players)")
        else:
            print(f"Question: {question_response.question_text}")
            print("Options:")
            for idx, option in enumerate(question_response.options):
                print(f"{idx + 1}. {option}")

            # Simulate choosing the first option
            selected_option = question_response.options[0]
            print(f"\nSubmitting answer: {selected_option}")

            # 3. Submit answer
            answer_result = await stub.SubmitAnswer(
                game_pb2.AnswerRequest(
                    player_id=player_id,
                    game_id=game_id,
                    question_id=question_response.question_id,
                    selected_option=selected_option
                )
            )
            print(f"Answer submitted. Correct: {answer_result.correct}, Points: {answer_result.points_awarded}")
            print(f"Explanation: {answer_result.explanation}")

        # 4. Get leaderboard
        leaderboard = await stub.GetLeaderboard(
            game_pb2.GameRequest(player_id=player_id, game_id=game_id)
        )
        print("\nLeaderboard:")
        for entry in leaderboard.entries:
            print(f"{entry.rank}. {entry.player_name} - {entry.score} pts")

if __name__ == "__main__":
    asyncio.run(run())
