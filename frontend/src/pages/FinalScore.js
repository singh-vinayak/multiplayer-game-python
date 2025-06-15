import React from 'react';
import { useNavigate } from 'react-router-dom';

function FinalScore() {
  const navigate = useNavigate();

  const goHome = () => {
    navigate('/');
  };

  return (
    <div>
      <h1>Game Over</h1>
      <p>Thanks for playing!</p>
      <button onClick={goHome}>Play Again</button>
    </div>
  );
}

export default FinalScore;
