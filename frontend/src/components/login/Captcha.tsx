import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { RefreshCw } from 'lucide-react';

interface CaptchaProps {
  onChange?: (code: string) => void;
}

export interface CaptchaRef {
  refresh: () => void;
  validate: (input: string) => boolean;
}

const Captcha = forwardRef<CaptchaRef, CaptchaProps>(({ onChange }, ref) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const codeRef = useRef<string>('');

  // 生成随机验证码
  const generateCode = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // 去除容易混淆的字符
    let code = '';
    for (let i = 0; i < 4; i++) {
      code += chars[Math.floor(Math.random() * chars.length)];
    }
    return code;
  };

  // 绘制验证码
  const drawCaptcha = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const code = generateCode();
    codeRef.current = code;
    
    if (onChange) {
      onChange(code);
    }

    // 设置画布尺寸
    const width = canvas.width;
    const height = canvas.height;

    // 清空画布 - 深色赛博朋克背景
    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, width, height);

    // 添加网格背景效果
    ctx.strokeStyle = 'rgba(99, 179, 237, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 0; i < width; i += 10) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, height);
      ctx.stroke();
    }
    for (let i = 0; i < height; i += 10) {
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(width, i);
      ctx.stroke();
    }

    // 绘制霓虹色干扰线
    const neonColors = ['#00f0ff', '#ff00ff', '#00ff00', '#ffff00', '#ff6b6b'];
    for (let i = 0; i < 5; i++) {
      ctx.strokeStyle = neonColors[Math.floor(Math.random() * neonColors.length)] + '40';
      ctx.lineWidth = Math.random() * 2 + 1;
      ctx.beginPath();
      ctx.moveTo(Math.random() * width, Math.random() * height);
      ctx.quadraticCurveTo(
        Math.random() * width,
        Math.random() * height,
        Math.random() * width,
        Math.random() * height
      );
      ctx.stroke();
    }

    // 绘制验证码字符
    const charWidth = width / 4;
    for (let i = 0; i < code.length; i++) {
      // 霓虹色文字
      const neonColor = neonColors[i % neonColors.length];
      
      // 字体设置
      ctx.font = `bold ${28 + Math.random() * 8}px 'Courier New', monospace`;
      
      // 文字发光效果
      ctx.shadowBlur = 10;
      ctx.shadowColor = neonColor;
      ctx.fillStyle = neonColor;
      
      // 随机旋转和位置
      const x = charWidth * i + charWidth / 2;
      const y = height / 2;
      const angle = (Math.random() - 0.5) * 0.4;
      
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      ctx.fillText(code[i], -10, 10);
      ctx.restore();
    }

    // 添加霓虹噪点
    for (let i = 0; i < 80; i++) {
      const x = Math.random() * width;
      const y = Math.random() * height;
      const color = neonColors[Math.floor(Math.random() * neonColors.length)];
      ctx.fillStyle = color + '60';
      ctx.fillRect(x, y, 2, 2);
    }

    // 重置阴影
    ctx.shadowBlur = 0;
  };

  // 刷新验证码
  const refresh = () => {
    drawCaptcha();
  };

  // 验证输入
  const validate = (input: string): boolean => {
    return input.toUpperCase() === codeRef.current.toUpperCase();
  };

  // 暴露方法给父组件
  useImperativeHandle(ref, () => ({
    refresh,
    validate
  }));

  // 初始化
  useEffect(() => {
    drawCaptcha();
  }, []);

  return (
    <div className="relative inline-block group">
      <canvas
        ref={canvasRef}
        width={140}
        height={50}
        className="rounded-lg border border-slate-700/50 cursor-pointer hover:border-cyan-500/50 transition-all duration-300"
        onClick={refresh}
      />
      <button
        type="button"
        onClick={refresh}
        className="absolute top-1 right-1 p-1.5 rounded-md bg-slate-800/80 hover:bg-slate-700/80 text-slate-400 hover:text-cyan-400 transition-all duration-300 opacity-0 group-hover:opacity-100"
        title="刷新验证码"
      >
        <RefreshCw className="w-3.5 h-3.5" />
      </button>
    </div>
  );
});

Captcha.displayName = 'Captcha';

export default Captcha;
