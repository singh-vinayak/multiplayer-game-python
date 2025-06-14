import asyncio
import uuid
from generated import game_pb2, game_pb2_grpc
from game.questions import QuestionBank

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
                "players": [],
                "questions": self.question_bank.get_all_questions(),
                "scores": {},
                "answered": {},
            }

        self.games[game_id]["players"].append({
            "id": player_id,
            "name": player_name,
        })
        self.players[player_id] = player_name
        self.player_game_map[player_id] = game_id
        self.games[game_id]["scores"][player_id] = 0
        self.games[game_id]["answered"][player_id] = []

        return game_pb2.JoinResponse(
            player_id=player_id,
            game_id=game_id,
            message=f"Player {player_name} joined game {game_id}"
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
        selected = request.selected_option

        game = self.games.get(game_id)
        if not game:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Game not found.")
            return game_pb2.AnswerResult()

        question = next((q for q in game["questions"] if q["question_id"] == question_id), None)
        if not question:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Question not found.")
            return game_pb2.AnswerResult()

        already_answered = question_id in game["answered"][player_id]
        if already_answered:
            return game_pb2.AnswerResult(correct=False, points_awarded=0, explanation="Already answered.")

        is_correct = selected == question["correct_option"]
        points = 10 if is_correct else 0
        if is_correct:
            game["scores"][player_id] += points

        game["answered"][player_id].append(question_id)
        await self._notify_leaderboard_update(game_id)

        return game_pb2.AnswerResult(
            correct=is_correct,
            points_awarded=points,
            explanation=question.get("explanation", "")
        )

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
        game_id = request.game_id

        if game_id not in self.leaderboard_streams:
            self.leaderboard_streams[game_id] = []

        queue = asyncio.Queue()
        self.leaderboard_streams[game_id].append(queue)

        try:
            while True:
                update = await queue.get()
                await context.write(update)
        except asyncio.CancelledError:
            self.leaderboard_streams[game_id].remove(queue)

    async def _notify_leaderboard_update(self, game_id):
        if game_id not in self.leaderboard_streams:
            return

        game = self.games[game_id]
        update = game_pb2.LeaderboardUpdate(
            leaderboard=game_pb2.Leaderboard(
                entries=self._generate_leaderboard_entries(game)
            )
        )

        for queue in self.leaderboard_streams[game_id]:
            await queue.put(update)

    def _generate_leaderboard_entries(self, game):
        scores = game["scores"]
        sorted_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        entries = []
        for rank, (player_id, score) in enumerate(sorted_players, start=1):
            entries.append(
                game_pb2.LeaderboardEntry(
                    player_id=player_id,
                    player_name=self.players[player_id],
                    score=score,
                    rank=rank
                )
            )
        return entries
