import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGame } from "../context/GameContext";
import { GameServiceClient } from "../grpc/game_grpc_web_pb";
import { JoinRequest } from "../grpc/game_pb";
import { Container, Card, Typography, TextField, Button } from '@mui/material';

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
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Card sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h4" gutterBottom>Join Game</Typography>
        <TextField
          label="Enter your name"
          variant="outlined"
          fullWidth
          margin="normal"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Button
          variant="contained"
          color="primary"
          fullWidth
          sx={{ mt: 2 }}
          onClick={handleJoin}
        >
          Join
        </Button>
      </Card>
    </Container>
  );
};

export default JoinGame;
