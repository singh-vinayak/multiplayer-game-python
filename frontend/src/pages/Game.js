import React, { useEffect, useState } from 'react';
import { GameServiceClient } from '../grpc/game_grpc_web_pb';
import {
  GameRequest,
  AnswerRequest
} from '../grpc/game_pb';
import { useGame } from '../context/GameContext';
import { useNavigate } from 'react-router-dom';
import {
  Container, Card, Typography, RadioGroup, FormControlLabel,
  Radio, Button, Box
} from '@mui/material';

const client = new GameServiceClient('http://localhost:8080', null, null);

function Game() {
  const { playerId, gameId } = useGame();
  const [question, setQuestion] = useState(null);
  const [selectedOption, setSelectedOption] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const fetchNextQuestion = () => {
    const request = new GameRequest();
    request.setGameId(gameId);
    request.setPlayerId(playerId);

    client.getNextQuestion(request, {}, (err, response) => {
      if (err) {
        console.error('GetNextQuestion error:', err.message);
        return;
      }

      if (!response.getQuestionText()) {
        setQuestion(null);  // Game over or waiting
        client.getLeaderboard(request, {}, (err, leaderboardResponse) => {
          if (err) {
            console.error('GetLeaderboard error:', err.message);
            return;
          }

          navigate('/leaderboard')
        });
        return;
      }

      setQuestion({
        id: response.getQuestionId(),
        text: response.getQuestionText(),
        options: response.getOptionsList()
      });
      setResult(null);
      setSelectedOption('');
    });
  };

  const submitAnswer = () => {
    if (!selectedOption || !question) return;

    setLoading(true);

    const answerReq = new AnswerRequest();
    answerReq.setGameId(gameId);
    answerReq.setPlayerId(playerId);
    answerReq.setQuestionId(question.id);
    answerReq.setSelectedOption(selectedOption);
    answerReq.setAnswerTimestamp(Date.now());

    client.submitAnswer(answerReq, {}, (err, res) => {
      setLoading(false);
      if (err) {
        console.error('SubmitAnswer error:', err.message);
        return;
      }

      setResult({
        correct: res.getCorrect(),
        points: res.getPointsAwarded(),
        explanation: res.getExplanation()
      });

      setTimeout(fetchNextQuestion, 5000);
    });
  };

  useEffect(() => {
    fetchNextQuestion();
  }, []);

  if (!question) return <h2>Waiting for next question...</h2>;

  return (
    <Container maxWidth="sm" sx={{ mt: 6 }}>
      {question ? (
        <Card sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom>
            {question.text}
          </Typography>
          <RadioGroup value={selectedOption} onChange={(e) => setSelectedOption(e.target.value)}>
            {question.options.map((option, i) => (
              <FormControlLabel key={i} value={option} control={<Radio />} label={option} />
            ))}
          </RadioGroup>
          <Button
            variant="contained"
            color="primary"
            onClick={submitAnswer}
            disabled={!selectedOption}
            sx={{ mt: 2 }}
          >
            Submit Answer
          </Button>

          {result && (
            <Box mt={3}>
              <Typography variant="body1" color={result.correct ? 'green' : 'red'}>
                {result.correct ? 'Correct!' : 'Incorrect.'}
              </Typography>
              <Typography variant="body2">{result.explanation}</Typography>
            </Box>
          )}
        </Card>
      ) : (
        <Card sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6">Waiting for next question or game over...</Typography>
          <Button sx={{ mt: 2 }} variant="outlined" onClick={() => window.location.href = '/leaderboard'}>
            View Leaderboard
          </Button>
        </Card>
      )}
    </Container>
  );
}

export default Game;
