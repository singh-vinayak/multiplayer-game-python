import React, { createContext, useContext, useState } from "react";

const GameContext = createContext();

export const useGame = () => useContext(GameContext);

export const GameProvider = ({ children }) => {
  const [playerId, setPlayerId] = useState(null);
  const [playerName, setPlayerName] = useState("");
  const [gameId, setGameId] = useState(null);

  return (
    <GameContext.Provider
      value={{ playerId, setPlayerId, playerName, setPlayerName, gameId, setGameId }}
    >
      {children}
    </GameContext.Provider>
  );
};
