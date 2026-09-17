import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';

interface MotionDrawerProps {
  direction?: 'left' | 'right';
  width?: number;
  backgroundColor?: string;
  clsBtnClassName?: string;
  contentClassName?: string;
  btnClassName?: string;
  children: React.ReactNode;
}

export const MotionDrawer: React.FC<MotionDrawerProps> = ({
  direction = 'left',
  width = 300,
  backgroundColor = '#ffffff',
  clsBtnClassName = '',
  contentClassName = '',
  btnClassName = '',
  children
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className={btnClassName || "p-2 rounded-full border border-slate-200 bg-white text-slate-800 shadow-sm"}
        aria-label="Open Navigation Drawer"
      >
        <Menu className="w-5 h-5" />
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex">
          <div 
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={() => setIsOpen(false)}
          />
          <div 
            className={`relative z-10 h-full p-6 shadow-2xl flex flex-col justify-between transition-transform duration-300 ${
              direction === 'left' ? 'left-0' : 'right-0'
            } ${contentClassName}`}
            style={{ width: `${width}px`, backgroundColor }}
          >
            <div>
              <div className="flex justify-between items-center mb-6">
                <button 
                  onClick={() => setIsOpen(false)}
                  className={`p-1.5 rounded-lg text-slate-600 hover:text-slate-900 ${clsBtnClassName}`}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              {children}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default MotionDrawer;
