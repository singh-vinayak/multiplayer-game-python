import React from "react";
import { useGame } from "../context/GameContext";
import { useNavigate } from "react-router-dom";
import { Container, Typography, Button, Card } from '@mui/material';

const Lobby = () => {
  const { playerId, playerName, gameId } = useGame();
  const navigate = useNavigate();

  const handleStart = () => {
    navigate("/game");
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Card sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Welcome to the Lobby, {playerName}!
        </Typography>
        <Typography variant="body1" gutterBottom>
          Game ID: {gameId}
        </Typography>
        <Button
          variant="contained"
          color="success"
          onClick={handleStart}
          sx={{ mt: 2 }}
        >
          Start Game
        </Button>
      </Card>
    </Container>
  );
};

export default Lobby;
