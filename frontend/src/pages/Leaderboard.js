import React, { useEffect, useState } from 'react';
import { Card, Typography, List, ListItem } from '@mui/material';
import { useGame } from '../context/GameContext';
import { GameServiceClient } from '../grpc/game_grpc_web_pb';
import { GameId } from '../grpc/game_pb';

const client = new GameServiceClient('http://localhost:8080', null, null);

function Leaderboard() {
  const { gameId } = useGame();
  const [entries, setEntries] = useState([]);

  useEffect(() => {
    client.getLeaderboard(new GameId().setGameId(gameId), {}, (err, response) => {
      setEntries(response.getEntriesList())
      // setEntries(update.getLeaderboard().getEntriesList());
    });
  }, []);

  return (
    <Card elevation={3} sx={{ padding: 2 }}>
      <Typography variant="h5" align="center">Leaderboard</Typography>
      <List>
        {entries.map((entry, i) => (
          <ListItem key={i}>
            {entry.getRank()}. {entry.getPlayerName()} - {entry.getScore()} pts
          </ListItem>
        ))}
      </List>
    </Card>
  );
}

export default Leaderboard;
