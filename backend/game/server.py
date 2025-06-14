import grpc
import asyncio
from concurrent import futures
from generated import game_pb2_grpc
from game.game_logic import GameServiceImpl

async def serve() -> None:
    server = grpc.aio.server()
    game_pb2_grpc.add_GameServiceServicer_to_server(GameServiceImpl(), server)
    server.add_insecure_port('0.0.0.0:50055')
    print("🚀 gRPC Game Server running at [::]:50055")
    await server.start()
    await server.wait_for_termination()
