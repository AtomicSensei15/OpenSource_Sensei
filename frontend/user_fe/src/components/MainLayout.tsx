import React from 'react';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface MainLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  title?: string;
  subtitle?: string;
  externalLink?: string;
  onBack?: () => void;
  className?: string;
}

const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  sidebar,
  title,
  subtitle,
  externalLink,
  onBack,
  className
}) => {
  return (
    <div className={cn("min-h-screen bg-slate-50 dark:bg-slate-900 flex", className)}>
      {/* Sidebar */}
      {sidebar && (
        <div className="flex-shrink-0">
          {sidebar}
        </div>
      )}
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        {(title || onBack) && (
          <header className="border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
            <div className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                {onBack && (
                  <Button onClick={onBack} variant="ghost" size="icon">
                    <ArrowLeft className="w-5 h-5" />
                  </Button>
                )}
                {title && (
                  <div>
                    <h1 className="text-xl font-semibold">{title}</h1>
                    {subtitle && (
                      <a 
                        href={externalLink} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="text-sm text-slate-500 hover:text-primary flex items-center gap-1"
                      >
                        {subtitle} <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>
          </header>
        )}
        
        {/* Main Content Area */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export default MainLayout;