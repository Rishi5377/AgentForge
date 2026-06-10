import { useState, useEffect } from 'react';

export type AgentState = 'idle' | 'working' | 'finished';

export function useAgentAnimation(activeAgent: string | null) {
  const [position, setPosition] = useState(50); // percentage 0 to 100
  const [direction, setDirection] = useState<'left' | 'right'>('right');
  const [state, setState] = useState<AgentState>('idle');

  useEffect(() => {
    if (!activeAgent) {
      setState('idle');
      return;
    }

    setState('working');
    
    // Pace back and forth while working
    const interval = setInterval(() => {
      setPosition((prev) => {
        let newPos = prev + (direction === 'right' ? 2 : -2);
        
        if (newPos >= 90) {
          setDirection('left');
          newPos = 90;
        } else if (newPos <= 10) {
          setDirection('right');
          newPos = 10;
        }
        return newPos;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [activeAgent, direction]);

  return { position, direction, state };
}
