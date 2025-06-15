import React, { useEffect, useState } from 'react';
import { GameServiceClient } from '../grpc/game_grpc_web_pb';
import {
  GameRequest,
  AnswerRequest
} from '../grpc/game_pb';
import { useGame } from '../context/GameContext';
import { useNavigate } from 'react-router-dom';

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
    <div>
      <h2>{question.text}</h2>
      {question.options.map((opt, index) => (
        <div key={index}>
          <label>
            <input
              type="radio"
              name="option"
              value={opt}
              checked={selectedOption === opt}
              onChange={() => setSelectedOption(opt)}
              disabled={!!result}
            />
            {opt}
          </label>
        </div>
      ))}
      <button onClick={submitAnswer} disabled={loading || !!result}>Submit</button>

      {result && (
        <div>
          <p>{result.correct ? '✅ Correct!' : '❌ Wrong'}</p>
          <p>Explanation: {result.explanation}</p>
          <p>+{result.points} points</p>
        </div>
      )}
    </div>
  );
}

export default Game;
