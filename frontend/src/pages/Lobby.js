import React from "react";
import { useGame } from "../context/GameContext";
import { useNavigate } from "react-router-dom";

const Lobby = () => {
  const { playerId, playerName, gameId } = useGame();
  const navigate = useNavigate();

  const handleStart = () => {
    navigate("/game");
  };

  return (
    <div>
      <h2>Lobby</h2>
      <p>Welcome, {playerName}</p>
      <p>Game ID: {gameId}</p>
      <button onClick={handleStart}>Start Game</button>
    </div>
  );
};

export default Lobby;
