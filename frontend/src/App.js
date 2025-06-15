import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import JoinGame from './pages/JoinGame';
import Lobby from './pages/Lobby';
import Game from './pages/Game';
import Leaderboard from './pages/Leaderboard';
import FinalScore from './pages/FinalScore';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<JoinGame />} />
        <Route path="/lobby" element={<Lobby />} />
        <Route path="/game" element={<Game />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/final" element={<FinalScore />} />
      </Routes>
    </Router>
  );
}

export default App;
