'use client'
import React from 'react'
import { ChevronRight } from 'lucide-react'
import { TimelineAnimation } from '@/components/ui/hero-financial-utils/timeline-animation'
import { EcommerceDash } from '@/components/ui/hero-financial-utils/assets-index'
import { useMediaQuery } from '@/components/ui/hero-financial-utils/use-media-query'
import MotionDrawer from '@/components/ui/hero-financial-utils/motion-drawer'

export const HeroFinancial = () => {
  const timelineRef = React.useRef<HTMLDivElement>(null)
  const isMobile = useMediaQuery('(max-width: 768px)')

  return (
    <section
      ref={timelineRef}
      className="min-h-screen bg-[#f7f9fc] text-[#1e293b] relative overflow-hidden flex flex-col items-center"
    >
      <div className="absolute inset-0 z-0 bg-[url('https://cdn.21st.dev/assets/mirror/f2/f2f40d6a9618bd458d2e195ccde0198a210e9700f51eb0e97976fcd984259b26.jpg')] bg-cover bg-center opacity-50" />

      <svg
        width="358"
        height="483"
        viewBox="0 0 358 483"
        className="absolute top-0 z-1 left-0 pointer-events-none"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <g filter="url(#filter0_f_0_1)">
          <rect
            x="-86.9961"
            y="-33.114"
            width="72"
            height="541"
            rx="36"
            transform="rotate(-30.8182 -86.9961 -33.114)"
            fill="url(#paint0_linear_0_1)"
          />
        </g>
        <g filter="url(#filter1_f_0_1)">
          <rect
            x="-17"
            y="-135.113"
            width="50.0937"
            height="541"
            rx="25.0469"
            transform="rotate(-30.8182 -17 -135.113)"
            fill="url(#paint1_linear_0_1)"
          />
        </g>
        <defs>
          <filter
            id="filter0_f_0_1"
            x="-137.641"
            y="-120.646"
            width="440.285"
            height="602.787"
            filterUnits="userSpaceOnUse"
            colorInterpolationFilters="sRGB"
          >
            <feFlood floodOpacity="0" result="BackgroundImageFix" />
            <feBlend
              mode="normal"
              in="SourceGraphic"
              in2="BackgroundImageFix"
              result="shape"
            />
            <feGaussianBlur
              stdDeviation="32"
              result="effect1_foregroundBlur_0_1"
            />
          </filter>
          <filter
            id="filter1_f_0_1"
            x="-71.707"
            y="-215.486"
            width="429.598"
            height="599.69"
            filterUnits="userSpaceOnUse"
            colorInterpolationFilters="sRGB"
          >
            <feFlood floodOpacity="0" result="BackgroundImageFix" />
            <feBlend
              mode="normal"
              in="SourceGraphic"
              in2="BackgroundImageFix"
              result="shape"
            />
            <feGaussianBlur
              stdDeviation="32"
              result="effect1_foregroundBlur_0_1"
            />
          </filter>
          <linearGradient
            id="paint0_linear_0_1"
            x1="-50.9961"
            y1="-33.114"
            x2="-50.9961"
            y2="507.886"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#91bbfb" />
            <stop offset="1" stopColor="#E6F1FF" />
          </linearGradient>
          <linearGradient
            id="paint1_linear_0_1"
            x1="8.04686"
            y1="-135.113"
            x2="8.04686"
            y2="405.887"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#8dbafd" />
            <stop offset="1" stopColor="#c1d9f8" />
          </linearGradient>
        </defs>
      </svg>

      {/* Soft Background Gradients */}
      <TimelineAnimation
        timelineRef={timelineRef}
        animationNum={5}
        className="absolute top-0 left-0 w-full h-[600px] bg-gradient-to-b from-blue-50 via-blue-100/40 to-transparent opacity-100 pointer-events-none"
      />
      {isMobile && (
        <div className="flex gap-4 justify-between items-center px-5 w-full pt-4 relative z-20">
          <MotionDrawer
            direction="left"
            width={300}
            backgroundColor={'#ffffff'}
            clsBtnClassName="bg-neutral-800 border-r border-neutral-900 text-white"
            contentClassName="bg-white border-r border-neutral-200 text-black"
            btnClassName="bg-white text-black relative w-fit p-2 left-0 top-0 rounded-full shadow-xs border border-neutral-200"
          >
            <nav className="space-y-4">
              <div className="flex items-center gap-2 text-black font-bold">
                <span>ROADSense AI</span>
              </div>
              <a href="#overview" className="block p-2 hover:bg-neutral-200 hover:text-black rounded-sm">
                Mission Overview
              </a>
              <a href="#gis" className="block p-2 hover:bg-neutral-200 hover:text-black rounded-sm">
                GIS Geospatial Map
              </a>
              <a href="#matrix" className="block p-2 hover:bg-neutral-200 hover:text-black rounded-sm">
                RCI Decision Matrix
              </a>
            </nav>
          </MotionDrawer>
          <button className="bg-neutral-900 text-white px-3 py-2 relative z-2 flex gap-1 items-center rounded-xl font-bold text-xs hover:bg-black transition shadow-sm">
            Launch Platform <ChevronRight size={16} />
          </button>
        </div>
      )}
      {/* Header */}
      {!isMobile && (
        <header className="relative z-10 w-full max-w-7xl mx-auto p-2 mt-4">
          <TimelineAnimation
            animationNum={1}
            timelineRef={timelineRef}
            className="bg-white/80 backdrop-blur-xl p-3 px-6 rounded-2xl border border-white/80 shadow-sm flex items-center justify-between"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center shadow-sm">
                <span className="text-white font-black text-sm">RS</span>
              </div>
              <span className="text-lg font-bold tracking-tight text-slate-900">
                ROADSense AI
              </span>
            </div>
            <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-slate-600">
              <a href="#overview" className="hover:text-blue-600 transition">Overview</a>
              <a href="#gis" className="hover:text-blue-600 transition">GIS Map</a>
              <a href="#matrix" className="hover:text-blue-600 transition">RCI Matrix</a>
              <a href="#copilot" className="hover:text-blue-600 transition">Copilot</a>
              <a href="#model" className="hover:text-blue-600 transition">ML Provenance</a>
            </nav>
            <button className="bg-slate-900 text-white px-4 py-2 flex gap-1.5 items-center rounded-xl font-bold text-xs hover:bg-black transition shadow-sm">
              Launch Platform <ChevronRight size={16} />
            </button>
          </TimelineAnimation>
        </header>
      )}
      {/* Hero Content */}
      <div className="relative z-10 text-center pt-16 pb-12 px-4 flex flex-col gap-5 max-w-5xl mx-auto">
        <TimelineAnimation
          animationNum={1}
          timelineRef={timelineRef}
          className="bg-white w-fit mx-auto text-slate-800 px-2 py-1 rounded-full inline-flex items-center gap-2 shadow-sm border border-slate-200"
        >
          <span className="bg-gradient-to-br from-blue-500 to-sky-400 text-white px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
            PARAKRAM 1.0
          </span>
          <span className="text-xs font-semibold text-slate-700">
            PK01PS001 — Spotting Trouble Before It Spreads
          </span>
        </TimelineAnimation>

        <TimelineAnimation
          as="h1"
          animationNum={2}
          timelineRef={timelineRef}
          className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-tight"
        >
          Intelligent Road Infrastructure <br />
          <span className="bg-gradient-to-r from-blue-600 via-sky-500 to-indigo-600 bg-clip-text text-transparent">
            Automated Damage Management
          </span>
        </TimelineAnimation>

        <TimelineAnimation
          as="p"
          animationNum={3}
          timelineRef={timelineRef}
          className="text-sm md:text-base text-slate-600 font-medium max-w-2xl mx-auto leading-relaxed"
        >
          Upload road dashcam footage for 12-stage frame extraction, YOLOv8 multi-class detection, ByteTrack spatial deduplication, deterministic RCI condition scoring, and TSP 2-Opt geodesic crew route optimization.
        </TimelineAnimation>
      </div>

      {/* Dashboard UI Frame */}
      <div className="w-full max-w-6xl mx-auto rounded-2xl relative mb-12 px-4">
        <TimelineAnimation
          animationNum={6}
          timelineRef={timelineRef}
          className="rounded-3xl bg-white/70 backdrop-blur-xl p-3 border border-white/80 shadow-xl"
        >
          <img
            src={EcommerceDash.src}
            alt={EcommerceDash.alt}
            className="w-full rounded-2xl shadow-inner border border-slate-200 object-cover max-h-[420px]"
          />
        </TimelineAnimation>
      </div>
    </section>
  )
}

export default HeroFinancial;
