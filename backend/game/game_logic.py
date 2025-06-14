import asyncio
import uuid
from generated import game_pb2, game_pb2_grpc
from game.questions import QuestionBank
import grpc

class GameServiceImpl(game_pb2_grpc.GameServiceServicer):
    def __init__(self):
        self.games = {}  # game_id -> game state
        self.players = {}  # player_id -> player name
        self.player_game_map = {}  # player_id -> game_id
        self.question_bank = QuestionBank()
        self.leaderboard_streams = {}  # game_id -> list of contexts

    async def JoinGame(self, request, context):
        player_id = str(uuid.uuid4())
        game_id = request.game_id or str(uuid.uuid4())  # new if not provided
        player_name = request.player_name

        if game_id not in self.games:
            self.games[game_id] = {
                "players": {player_id: {"name": player_name, "score": 0, "answers": set()}},
                "questions": self.question_bank.get_all_questions(),
                "current_question_index": 0,
                "answered_players": {},  # Track answers per question
                "leaderboard_listeners": [],
                "completed": False,
            }
        else:
            self.games[game_id]["players"][player_id] = {
                "name": player_name,
                "score": 0,
                "answers": set()
            }

        return game_pb2.JoinResponse(
            player_id=player_id,
            game_id=game_id,
            message=f"{player_name} joined game {game_id}"
        )



    async def StartGame(self, request, context):
        game_id = request.game_id
        player_id = request.player_id

        game = self.games.get(game_id)
        if not game:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Game not found.")
            return

        questions = game["questions"]
        for q in questions:
            await context.write(
                game_pb2.QuestionCard(
                    question_id=q["question_id"],
                    question_text=q["question_text"],
                    options=q["options"],
                    time_limit_seconds=10
                )
            )
            await asyncio.sleep(10)  # Simulate 10 sec wait

    async def SubmitAnswer(self, request, context):
        game_id = request.game_id
        player_id = request.player_id
        question_id = request.question_id
        selected_option = request.selected_option

        game = self.games.get(game_id)
        if not game or player_id not in game["players"]:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Game or player not found")
            return game_pb2.AnswerResult()

        question_list = game["questions"]
        current_index = game["current_question_index"]

        if current_index >= len(question_list):
            return game_pb2.AnswerResult(correct=False, points_awarded=0, explanation="Game has ended.")

        current_question = question_list[current_index]
        correct_option = current_question["correct_option"]
        explanation = current_question.get("explanation", "")

        # Ensure tracking structure exists
        if question_id not in game["answered_players"]:
            game["answered_players"][question_id] = set()

        # Prevent multiple answers
        if player_id in game["answered_players"][question_id]:
            return game_pb2.AnswerResult(correct=False, points_awarded=0, explanation="Already answered.")

        # Record answer
        game["answered_players"][question_id].add(player_id)

        correct = selected_option == correct_option
        points = 10 if correct else 0
        game["players"][player_id]["score"] += points

        # Send updated leaderboard
        # await self._notify_leaderboard_update(game)

        # Check if all players answered this question
        if len(game["answered_players"][question_id]) == len(game["players"]):
            game["current_question_index"] += 1
            if game["current_question_index"] >= len(game["questions"]):
                game["completed"] = True
                await self._broadcast_final_leaderboard(game)

        return game_pb2.AnswerResult(correct=correct, points_awarded=points, explanation=explanation)


    async def GetLeaderboard(self, request, context):
        game_id = request.game_id
        game = self.games.get(game_id)
        if not game:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Game not found.")
            return game_pb2.Leaderboard()

        entries = self._generate_leaderboard_entries(game)
        return game_pb2.Leaderboard(entries=entries)

    async def StreamLeaderboard(self, request, context):
        game = self.games.get(request.game_id)
        if not game:
            return

        queue = asyncio.Queue()
        game["leaderboard_listeners"].append(queue)

        while True:
            update = await queue.get()
            yield update
            if update.game_over:
                break


    async def _notify_leaderboard_update(self, game):
        if not game:
            return

        update = game_pb2.LeaderboardUpdate(
            leaderboard=game_pb2.Leaderboard(
                entries=self._generate_leaderboard_entries(game)
            ),
            game_over=game.get("completed", False)
        )

        for queue in game["leaderboard_listeners"]:
            await queue.put(update)

    def _generate_leaderboard_entries(self, game):
        players = game["players"]

        # Sort players by score descending
        sorted_players = sorted(
            players.items(),
            key=lambda item: item[1]["score"],
            reverse=True
        )

        entries = []
        for rank, (player_id, player_data) in enumerate(sorted_players, start=1):
            entries.append(
                game_pb2.LeaderboardEntry(
                    player_id=player_id,
                    player_name=player_data["name"],
                    score=player_data["score"],
                    rank=rank
                )
            )

        return entries

    async def _broadcast_final_leaderboard(self, game):
        update = game_pb2.LeaderboardUpdate(
            leaderboard=self._build_leaderboard(game),
            game_over=True
        )
        for queue in game["leaderboard_listeners"]:
            await queue.put(update)
    def _build_leaderboard(self, game):
        sorted_players = sorted(
            game["players"].items(),
            key=lambda item: item[1]["score"],
            reverse=True
        )

        entries = []
        for rank, (player_id, info) in enumerate(sorted_players, start=1):
            entry = game_pb2.LeaderboardEntry(
                player_id=player_id,
                player_name=info["name"],
                score=info["score"],
                rank=rank
            )
            entries.append(entry)

        return game_pb2.Leaderboard(entries=entries)
