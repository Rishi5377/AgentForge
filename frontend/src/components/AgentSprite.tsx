import { useState, useEffect } from 'react';
import { AgentState } from '@/hooks/useAgentAnimation';

interface AgentSpriteProps {
  agentName: string;
  position: number;
  direction: 'left' | 'right';
  state: AgentState;
}

// Configuration map mapping each agent to its specific sprite sheet grid logic
const agentConfigs: Record<string, { url: string, cols: number, rows: number, speed: number }> = {
  frontend: { url: '/frontend_test.png', cols: 6, rows: 5, speed: 70 },
  validator: { url: '/validator_test.png', cols: 6, rows: 5, speed: 50 },
  backend: { url: '/backend_test.png', cols: 5, rows: 4, speed: 50 },
  database: { url: '/database_test.png', cols: 5, rows: 4, speed: 50 },
  supervisor: { url: '/sprite_sheet_192_5px.png', cols: 6, rows: 5, speed: 75 },
  orchestrator: { url: '/orchestrator_test.png', cols: 5, rows: 4, speed: 50 },
  assembler: { url: '/validator_test.png', cols: 6, rows: 5, speed: 50 },
  system: { url: '/validator_test.png', cols: 6, rows: 5, speed: 50 },
};

export default function AgentSprite({ agentName, position, direction, state }: AgentSpriteProps) {
  const [currentFrame, setCurrentFrame] = useState(0);

  // Default to orchestrator.png if an agent isn't explicitly listed
  const config = agentConfigs[agentName.toLowerCase()] || agentConfigs.orchestrator;

  useEffect(() => {
    // If the agent is idle, we don't need to run the animation interval
    if (state === 'idle') return;

    const totalFrames = config.cols * config.rows;
    const intervalId = setInterval(() => {
      setCurrentFrame((prev) => (prev + 1) % totalFrames);
    }, config.speed);

    // Cleanup the interval when the component unmounts or state changes
    return () => clearInterval(intervalId);
  }, [state, config.cols, config.rows, config.speed]);

  if (state === 'idle') return null;

  // Calculate the background position percentages based on the current frame
  const x = currentFrame % config.cols;
  const y = Math.floor(currentFrame / config.cols);
  const xPos = config.cols > 1 ? x * (100 / (config.cols - 1)) : 0;
  const yPos = config.rows > 1 ? y * (100 / (config.rows - 1)) : 0;

  return (
    <div
      className="absolute bottom-0 left-4 flex flex-col items-center z-50 pointer-events-auto"
    >
      <div
        className="bg-[#090909] text-[#0099ff] border border-[#0099ff]/30 text-[10px] px-3 py-1 rounded-full ring-shadow-blue shadow-[0_0_15px_rgba(0,153,255,0.2)] mb-2 whitespace-nowrap uppercase tracking-wider font-bold"
      >
        {agentName}
      </div>

      {/* Sprite Container without the circle frame */}
      <div className="w-16 h-16 drop-shadow-[0_0_15px_rgba(0,153,255,0.4)]">
        <div
          className="w-full h-full bg-no-repeat"
          style={{
            backgroundImage: `url('${config.url}')`,
            backgroundSize: `${config.cols * 100}% ${config.rows * 100}%`,
            backgroundPosition: `${xPos}% ${yPos}%`,
            imageRendering: "pixelated"
          }}
        />
      </div>
    </div>
  );
}
