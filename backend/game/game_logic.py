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


    async def GetNextQuestion(self, request, context):
        game_id = request.game_id
        player_id = request.player_id
        game = self.games.get(game_id)
        if not game:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Game or player not found")
            return game_pb2.QuestionCard()

        if game["completed"]:
            return game_pb2.QuestionCard()

        questions = game["questions"]
        current_index = game["current_question_index"]
        players = game["players"]
        total_players = len(players)

        # If no more questions, return empty
        if current_index >= len(questions):
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No more questions")
            return game_pb2.QuestionCard()

        current_question = questions[current_index]
        question_id = current_question["question_id"]

        # Wait until all players have answered the current question before advancing
        answered_players = game["answered_players"].get(question_id, set())

        if len(answered_players) < total_players:
            # Still waiting for others to answer
            return game_pb2.QuestionCard(
                question_id=question_id,
                question_text=current_question["question_text"],
                options=current_question["options"]
            )
        else:
            # All players answered — advance to next question
            game["current_question_index"] += 1
            if game["current_question_index"] >= len(questions):
                return game_pb2.Question()  # Game over

            next_question = questions[game["current_question_index"]]
            return game_pb2.QuestionCard(
                question_id=next_question["question_id"],
                question_text=next_question["question_text"],
                options=next_question["options"]
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
            print(f"Sending question to player {player_id}: {q["question_text"]}")
            await context.write(
                game_pb2.QuestionCard(
                    question_id=q["question_id"],
                    question_text=q["question_text"],
                    options=q["options"],
                    time_limit_seconds=10
                )
            )
            # await asyncio.sleep(10)  # Simulate 10 sec wait

    async def SubmitAnswer(self, request, context):
        game_id = request.game_id
        player_id = request.player_id
        selected_option = request.selected_option

        game = self.games.get(game_id)
        if not game or player_id not in game["players"]:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Game or player not found")
            return game_pb2.AnswerResult()

        current_index = game["current_question_index"]
        if current_index >= len(game["questions"]):
            return game_pb2.AnswerResult(correct=False, points_awarded=0, explanation="Game has ended.")

        question = game["questions"][current_index]
        question_id = question["question_id"]
        correct_option = question["correct_option"]
        explanation = question.get("explanation", "")

        # Ensure answered_players structure exists
        if question_id not in game["answered_players"]:
            game["answered_players"][question_id] = set()

        # Prevent duplicate answers
        if player_id in game["answered_players"][question_id]:
            return game_pb2.AnswerResult(correct=False, points_awarded=0, explanation="Already answered.")

        # Record the player's answer
        game["answered_players"][question_id].add(player_id)

        correct = selected_option == correct_option
        points = 10 if correct else 0
        game["players"][player_id]["score"] += points

        # Optionally send updated leaderboard here
        # await self._notify_leaderboard_update(game)

        # If all players have answered this question
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
