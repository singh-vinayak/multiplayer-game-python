import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGame } from "../context/GameContext";
import { GameServiceClient } from "../grpc/game_grpc_web_pb";
import { JoinRequest } from "../grpc/game_pb";

const client = new GameServiceClient("http://localhost:8080", null, null);

const JoinGame = () => {
  const [name, setName] = useState("");
  const navigate = useNavigate();
  const { setPlayerId, setPlayerName, setGameId } = useGame();

  const handleJoin = () => {
    const request = new JoinRequest();
    request.setPlayerName(name);

    client.joinGame(request, {}, (err, response) => {
      if (err) {
        console.error(err);
        alert("Failed to join game");
        return;
      }

      setPlayerId(response.getPlayerId());
      setPlayerName(name);
      setGameId(response.getGameId());

      navigate("/lobby");
    });
  };

  return (
    <div>
      <h2>Join Game</h2>
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Enter name" />
      <button onClick={handleJoin}>Join</button>
    </div>
  );
};

export default JoinGame;
