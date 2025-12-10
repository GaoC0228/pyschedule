import React, { useState, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { User, Lock, ArrowRight, Terminal, Shield } from 'lucide-react';
import { message } from 'antd';
import { useAuth } from '../contexts/AuthContext';
import { Background } from '../components/login/Background';
import { Input } from '../components/login/Input';
import { Button } from '../components/login/Button';
import { Typewriter } from '../components/login/Typewriter';
import Captcha, { CaptchaRef } from '../components/login/Captcha';

const dailyQuotes = [
  "代码编织未来，自动化解放思维。",
  "每一次自动化，都是对重复劳动的解放。",
  "优雅的代码，源于对细节的执着。",
  "定时任务，让系统在睡梦中为你工作。",
  "Python的禅意：简单优于复杂。"
];

export default function LoginNew() {
  const [isLoading, setIsLoading] = useState(false);
  const [formState, setFormState] = useState({
    username: '',
    password: '',
    captcha: ''
  });
  const [error, setError] = useState('');
  const [captchaError, setCaptchaError] = useState('');
  
  const navigate = useNavigate();
  const { login } = useAuth();
  const captchaRef = useRef<CaptchaRef>(null);
  
  // 使用useMemo确保每日寄语不会每次渲染都变化
  const quote = useMemo(() => dailyQuotes[Math.floor(Math.random() * dailyQuotes.length)], []);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation(); // 阻止事件冒泡
    
    setError('');
    setCaptchaError('');
    
    // 验证码校验
    if (!captchaRef.current?.validate(formState.captcha)) {
      setCaptchaError('验证码错误');
      captchaRef.current?.refresh();
      setFormState({ ...formState, captcha: '' });
      return;
    }
    
    setIsLoading(true);
    
    try {
      await login(formState.username, formState.password);
      message.success('登录成功！正在跳转至控制台...', 2);
      
      // 只在成功时才清空表单
      setFormState({ username: '', password: '', captcha: '' });
      
      setTimeout(() => {
        navigate('/dashboard');
      }, 500);
    } catch (error: any) {
      // 详细错误处理
      let errorMessage = '登录失败';
      
      if (error.response) {
        errorMessage = error.response.data?.detail || error.response.data?.message || '登录失败，请重试';
      } else if (error.request) {
        errorMessage = '网络连接失败，请检查网络';
      } else {
        errorMessage = error.message || '登录失败，请重试';
      }
      
      // 登录失败时不清空表单，保留用户输入
      // 只显示输入框下方的错误提示，不显示顶部弹框
      setError(errorMessage);
      console.error('登录错误:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center relative p-4 sm:p-8">
      <Background />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-8 z-10"
      >
        {/* Left Side: Branding & Info */}
        <div className="hidden lg:flex flex-col justify-center space-y-8 p-8 relative">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-2"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-900/30">
                <Terminal className="w-6 h-6 text-white" />
              </div>
              <span className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                PySchedule
              </span>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="space-y-6"
          >
            {/* Merged Title with Gradient */}
            <div className="text-5xl font-bold tracking-tight leading-tight h-[120px]">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-200 to-blue-500">
                <Typewriter 
                  text="自动化任务智能调度中心" 
                  loop 
                  speed={150} 
                  delay={5000} 
                  deleteSpeed={50}
                />
              </span>
            </div>
            
            {/* Dynamic Quote Section */}
            <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm relative overflow-hidden group min-h-[100px] flex flex-col justify-center">
               <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"/>
               <div className="text-lg text-slate-300 font-light italic relative z-10 leading-relaxed">
                 <Typewriter text={quote} speed={80} loop={false} />
               </div>
            </div>
          </motion.div>

          <div className="text-sm text-slate-500">
            2025 Python定时任务管理系统
          </div>
        </div>

        {/* Right Side: Auth Form */}
        <div className="flex items-center justify-center">
          <motion.div 
            layout
            className="w-full max-w-md bg-slate-900/40 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl shadow-black/50 relative overflow-hidden"
          >
            {/* Decorative top sheen */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-50" />
            
            <div className="mb-8 text-center lg:text-left">
              <h2 className="text-2xl font-bold text-white mb-2">
                管理员登录
              </h2>
              <p className="text-slate-400 text-sm">
                请输入您的账号与密码以访问控制台
              </p>
            </div>

            <form onSubmit={handleAuth} className="space-y-5">
              <Input 
                label="账号" 
                placeholder="admin"
                type="text"
                icon={<User className="w-5 h-5" />}
                required
                value={formState.username}
                onChange={(e) => setFormState({...formState, username: e.target.value})}
              />

              <div className="space-y-1">
                <Input 
                  label="密码" 
                  placeholder="••••••••"
                  type="password"
                  icon={<Lock className="w-5 h-5" />}
                  required
                  value={formState.password}
                  onChange={(e) => setFormState({...formState, password: e.target.value})}
                  error={error}
                />
              </div>

              {/* 验证码 */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-300 ml-1">
                  安全验证
                </label>
                <div className="flex gap-3 items-start">
                  <div className="flex-1">
                    <div className="relative group">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 group-focus-within:text-cyan-400 transition-colors duration-300">
                        <Shield className="w-5 h-5" />
                      </div>
                      <input
                        type="text"
                        placeholder="请输入验证码"
                        required
                        value={formState.captcha}
                        onChange={(e) => setFormState({...formState, captcha: e.target.value.toUpperCase()})}
                        className={`
                          w-full bg-slate-900/50 text-white placeholder-slate-500
                          border border-slate-700/50 rounded-xl py-3 pl-10 pr-4
                          focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50
                          transition-all duration-300 hover:bg-slate-900/70 hover:border-slate-600
                          ${captchaError ? 'border-red-500/50 focus:ring-red-500/20' : ''}
                        `}
                        maxLength={4}
                      />
                    </div>
                    {captchaError && (
                      <p className="text-xs text-red-400 ml-1 mt-1.5 animate-pulse">
                        {captchaError}
                      </p>
                    )}
                  </div>
                  <Captcha ref={captchaRef} />
                </div>
              </div>

              <Button type="submit" isLoading={isLoading} className="mt-2">
                登录系统
                {!isLoading && <ArrowRight className="w-5 h-5 ml-1" />}
              </Button>
            </form>
            
            {/* Footer decoration */}
            <div className="mt-8 pt-6 border-t border-white/5 flex justify-center text-xs text-slate-600 gap-4">
              <span>系统状态: 正常</span>
              <span>•</span>
              <span>节点: CN-HQ-01</span>
            </div>
          </motion.div>
        </div>
      </motion.div>
      
      {/* Mobile Branding */}
      <div className="lg:hidden absolute top-6 left-6 flex items-center gap-2">
         <Terminal className="w-6 h-6 text-cyan-400" />
         <span className="font-bold text-white tracking-tight">PySchedule</span>
      </div>
    </div>
  );
}
