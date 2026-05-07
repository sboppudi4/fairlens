import { motion } from "framer-motion";

interface Props {
  score: number; // 0-100
  riskLevel: string;
  size?: number;
}

export default function FairnessGauge({ score, riskLevel, size = 180 }: Props) {
  const clamped = Math.max(0, Math.min(100, score));
  const tone =
    clamped >= 80
      ? { ring: "stroke-success", text: "text-success" }
      : clamped >= 60
        ? { ring: "stroke-warning", text: "text-warning" }
        : { ring: "stroke-danger", text: "text-danger" };

  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = (clamped / 100) * circumference;

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Fairness score ${clamped} out of 100, ${riskLevel}`}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          className="stroke-border fill-transparent"
          strokeWidth={10}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          className={`fill-transparent ${tone.ring}`}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference - dash }}
          transition={{ duration: 0.9, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className={`font-mono text-4xl font-bold ${tone.text}`}>{clamped.toFixed(0)}</div>
        <div className={`text-xs uppercase tracking-wider ${tone.text}`}>{riskLevel}</div>
      </div>
    </div>
  );
}
