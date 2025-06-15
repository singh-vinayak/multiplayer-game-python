import React, { useEffect, useState } from 'react';
import { useGame } from '../context/GameContext';
import { GameServiceClient } from '../grpc/game_grpc_web_pb';
import { GameId } from '../grpc/game_pb';

const client = new GameServiceClient('http://localhost:8080', null, null);

function Leaderboard() {
  const { gameId } = useGame();
  const [entries, setEntries] = useState([]);

  useEffect(() => {
    client.getLeaderboard(new GameId().setGameId(gameId),{}, (err, response) => {
      setEntries(response.getEntriesList())
      // setEntries(update.getLeaderboard().getEntriesList());
    });
  }, []);

  return (
    <div>
      <h2>Leaderboard</h2>
      <ul>
        {entries.map((entry, i) => (
          <li key={i}>
            {entry.getRank()}. {entry.getPlayerName()} - {entry.getScore()} pts
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Leaderboard;
