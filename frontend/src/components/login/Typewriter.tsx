import React, { useState, useEffect } from 'react';

interface TypewriterProps {
  text: string;
  speed?: number;
  deleteSpeed?: number;
  delay?: number;
  loop?: boolean;
  className?: string;
}

export const Typewriter: React.FC<TypewriterProps> = ({ 
  text, 
  speed = 150, 
  deleteSpeed = 100,
  delay = 3000,
  loop = false,
  className = '' 
}) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;

    const handleTyping = () => {
      const currentLen = displayedText.length;
      
      // Typing Phase
      if (!isDeleting && currentLen < text.length) {
        setDisplayedText(text.substring(0, currentLen + 1));
        timer = setTimeout(handleTyping, speed);
      } 
      // Finished Typing, Waiting to Delete
      else if (!isDeleting && currentLen === text.length) {
        if (loop) {
          timer = setTimeout(() => {
            setIsDeleting(true);
            handleTyping();
          }, delay);
        }
      } 
      // Deleting Phase
      else if (isDeleting && currentLen > 0) {
        setDisplayedText(text.substring(0, currentLen - 1));
        timer = setTimeout(handleTyping, deleteSpeed);
      } 
      // Finished Deleting, Waiting to Type
      else if (isDeleting && currentLen === 0) {
        setIsDeleting(false);
        timer = setTimeout(handleTyping, 500);
      }
    };

    // Initial start or resume
    timer = setTimeout(handleTyping, 100);

    return () => clearTimeout(timer);
  }, [displayedText, isDeleting, loop, text, speed, deleteSpeed, delay]);

  return (
    <span className={className}>
      {displayedText}
      <span className="animate-pulse border-r-2 border-cyan-400 ml-1 inline-block h-[1em] align-middle transform translate-y-[-2px]">&nbsp;</span>
    </span>
  );
};
