import React, { useState, useEffect, useMemo } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import {
  Activity, Bell, LayoutDashboard, Users, ClipboardCheck,
  Calendar, FileText, Search, Heart, Moon, Sun, Dumbbell,
} from 'lucide-react';
import { GlobalSearch } from './GlobalSearch';
import { RecoveryModule } from './RecoveryModule';
import { getUnreadAlertCount } from '../services/api';

const navItems = [
  { path: '/',             label: '仪表板',     icon: LayoutDashboard },
  { path: '/athletes',     label: '运动员',     icon: Users },
  { path: '/training-log', label: '训练日志',   icon: ClipboardCheck },
  { path: '/planner',      label: '训练计划',   icon: Calendar },
  { path: '/exercises',    label: '动作库',     icon: Dumbbell },
  { path: '/alerts',       label: '预警中心',   icon: Bell },
  { path: '/rehab',        label: '康复中心',   icon: Heart },
  { path: '/reports',      label: '报告',       icon: FileText },
];

function ClockIcon() {
  return (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

type ThemeMode = 'auto' | 'dark' | 'light';

function getCurrentTheme(): ThemeMode {
  return (localStorage.getItem('athleteiq-theme') as ThemeMode) || 'auto';
}

function getEffectiveDark(): boolean {
  const mode = getCurrentTheme();
  if (mode === 'dark') return true;
  if (mode === 'light') return false;
  const hour = new Date().getHours();
  return hour >= 18 || hour < 6;
}

function setTheme(mode: ThemeMode) {
  if (mode === 'auto') {
    localStorage.removeItem('athleteiq-theme');
  } else {
    localStorage.setItem('athleteiq-theme', mode);
  }
  const useDark = getEffectiveDark();
  document.documentElement.classList.toggle('dark', useDark);
  return useDark;
}

export function Layout({ children }: React.PropsWithChildren) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [theme, setThemeState] = useState<ThemeMode>(getCurrentTheme());
  const [isDark, setIsDark] = useState(document.documentElement.classList.contains('dark'));
  const location = useLocation();

  useEffect(() => {
    getUnreadAlertCount()
      .then((data) => setUnreadCount(data.unread_count))
      .catch(() => {});
    const interval = setInterval(() => {
      getUnreadAlertCount()
        .then((data) => setUnreadCount(data.unread_count))
        .catch(() => {});
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  // Re-check auto mode every 10 minutes
  useEffect(() => {
    const timer = setInterval(() => {
      if (getCurrentTheme() === 'auto') {
        const effective = getEffectiveDark();
        if (effective !== isDark) {
          setIsDark(effective);
          document.documentElement.classList.toggle('dark', effective);
        }
      }
    }, 600000); // every 10 min
    return () => clearInterval(timer);
  }, [isDark]);

  const toggleDark = () => {
    const modes: ThemeMode[] = ['auto', 'dark', 'light'];
    const idx = modes.indexOf(theme);
    const next = modes[(idx + 1) % 3];
    setThemeState(next);
    const effective = setTheme(next);
    setIsDark(effective);
  };

  const currentPage = navItems.find(i =>
    location.pathname === i.path || (i.path !== '/' && location.pathname.startsWith(i.path))
  );

  // Extract athlete ID from URL for sidebar recovery module
  const sidebarAthleteId = useMemo(() => {
    const match = location.pathname.match(/^\/athletes\/([a-f0-9-]+)/);
    return match ? match[1] : '';
  }, [location.pathname]);

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950">
      {/* Sidebar */}
      <aside className="w-[212px] shrink-0 flex flex-col bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-r border-slate-200 dark:border-slate-800">
        {/* Logo */}
        <div className="px-5 py-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-[10px] bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center shadow-sm shadow-cyan-500/25">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-[15px] font-bold text-slate-900 dark:text-slate-100 leading-none tracking-tight">AthleteIQ</h1>
              <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">运动科学平台</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 space-y-0.5">
          <p className="px-3 py-2 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest">导航</p>
          {navItems.map(item => {
            const Icon = item.icon;
            const active = location.pathname === item.path
              || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-[14px] font-medium transition-all duration-150 ${
                  active
                    ? 'bg-cyan-500 text-white shadow-sm shadow-cyan-500/25'
                    : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <Icon className="w-[18px] h-[18px] shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Recovery module for athlete detail pages */}
        {sidebarAthleteId && (
          <div className="px-3 py-3 border-t border-slate-200 dark:border-slate-800 max-h-[360px] overflow-y-auto">
            <RecoveryModule athleteId={sidebarAthleteId} />
          </div>
        )}

        {/* Search trigger */}
        <div className="px-3 py-4 border-t border-slate-200 dark:border-slate-800">
          <button
            onClick={() => setSearchOpen(true)}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 text-[13px] hover:bg-slate-200 dark:hover:bg-slate-700 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
          >
            <Search className="w-[15px] h-[15px]" />
            搜索...
            <kbd className="ml-auto text-[10px] font-mono bg-white/60 dark:bg-slate-700 px-1.5 py-0.5 rounded-md">⌘K</kbd>
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-11 shrink-0 flex items-center justify-between px-6 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2 text-[13px]">
            <span className="font-semibold text-slate-900 dark:text-slate-100">{currentPage?.label || 'AthleteIQ'}</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleDark}
              className="flex items-center gap-1 px-2 py-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-[11px] text-slate-400 dark:text-slate-500"
              title={theme === 'auto' ? '自动模式（18:00切换）· 点击切换' : theme === 'dark' ? '夜间模式 · 点击切换' : '日间模式 · 点击切换'}
            >
              {theme === 'auto' ? (
                <><span className="font-bold text-slate-500 dark:text-slate-400">AUTO</span><ClockIcon /></>
              ) : theme === 'dark' ? (
                <><Sun className="w-3.5 h-3.5 text-amber-400" /><span>暗</span></>
              ) : (
                <><Moon className="w-3.5 h-3.5 text-slate-400" /><span>亮</span></>
              )}
            </button>
            <Link to="/alerts" className="relative p-1.5 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
              <Bell className="w-[17px] h-[17px] text-slate-400 dark:text-slate-500" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-white dark:ring-slate-900 px-1">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <div className="max-w-[1200px] mx-auto p-6 animate-fade-in">
            {children}
          </div>
        </main>
      </div>

      <GlobalSearch open={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}
