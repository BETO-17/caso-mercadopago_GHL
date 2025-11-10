import { useEffect, useState } from 'react';

function Alert({ message, type = "success", duration = 3000, onClose }) {
  const [isVisible, setIsVisible] = useState(true);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    // Animación de la barra de progreso
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev - (100 / (duration / 50));
        return newProgress > 0 ? newProgress : 0;
      });
    }, 50);

    // Timer para ocultar la alerta
    const timer = setTimeout(() => {
      setIsVisible(false);
      if (onClose) onClose();
    }, duration);

    return () => {
      clearInterval(progressInterval);
      clearTimeout(timer);
    };
  }, [duration, onClose]);

  if (!isVisible) return null;

  const bgColor = type === "success" 
    ? "bg-gradient-button" 
    : "bg-red-500";

  const icon = type === "success" 
    ? "✓" 
    : "✕";

  return (
    <div className={`fixed top-8 left-1/2 -translate-x-1/2 z-[200] animate-fade-in-down`}>
      <div className={`${bgColor} text-text-primary px-8 py-4 rounded-xl shadow-2xl min-w-[300px] max-w-[500px]`}>
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold">{icon}</span>
          <p className="font-medium text-base">{message}</p>
        </div>
        {/* Barra de progreso */}
        <div className="mt-3 h-1 bg-white/20 rounded-full overflow-hidden">
          <div 
            className="h-full bg-white transition-all duration-50 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default Alert;
