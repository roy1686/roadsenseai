import React, { useState } from 'react';
import { 
  Shield, Video, MapPin, Layers, Navigation, Bot, Cpu, 
  Sparkles, ArrowRight, CheckCircle2, Play, Activity, 
  FileText, Zap, Award, BarChart3, Database, ShieldCheck,
  Compass, ExternalLink, RefreshCw, Check, ArrowUpRight,
  Eye, CornerDownRight, Milestone, Clock, CheckSquare
} from 'lucide-react';

export default function LandingHero({
  onEnterDashboard,
  onRunSampleDemo,
  onRunCleanDemo,
  onOpenGis,
  onOpenStudio,
  onOpenCopilot,
  onOpenMatrix,
  onOpenRoutes
}) {
  const [activeFeatureTab, setActiveFeatureTab] = useState('cv');

  const featureTabs = [
    {
      id: 'cv',
      title: 'Computer Vision AI',
      subtitle: 'YOLOv8 & Kalman ByteTrack',
      icon: Video,
      color: 'from-sky-500 to-blue-600',
      badge: 'Edge-Inference Ready',
      desc: 'Sub-second multi-class pavement distress detection fine-tuned on the RDD2022 dataset with Laplacian blur QA filtering and continuous bounding box tracking.',
      highlights: [
        'Multi-Class Detection: Potholes, Alligator, Transverse & Longitudinal Cracks',
        'ByteTrack Object Tracking with Kalman filtering to eliminate duplicate counting',
        'Laplacian variance QA to automatically discard uncalibrated or blurred frames',
        'Web-Standard H.264 MP4 rendering with real-time HUD telemetry banners'
      ],
      actionText: 'Launch Dashcam Studio',
      action: onOpenStudio || onEnterDashboard
    },
    {
      id: 'gis',
      title: '3-Layer GIS Center',
      subtitle: 'OpenStreetMap & Esri Satellite',
      icon: MapPin,
      color: 'from-emerald-500 to-teal-600',
      badge: 'Coordinate Pinning',
      desc: 'High-precision geospatial defect mapping with automatic EXIF telemetry extraction, interactive layer toggles, and click-to-frame video synchronization.',
      highlights: [
        'Dynamic map tiling: OpenStreetMap, Esri High-Res Satellite & Carto Topographic',
        'Click-to-frame synchronization: Click any defect pin to seek video to that timestamp',
        'Severity color coding: Critical P1 (Red), High P2 (Orange), Moderate P3 (Yellow)',
        'Corridor bounding box clustering and GeoJSON export for municipal GIS systems'
      ],
      actionText: 'Open GIS Command',
      action: onOpenGis || onEnterDashboard
    },
    {
      id: 'rci',
      title: 'Deterministic RCI Matrix',
      subtitle: 'MoRTH Compliance Standard',
      icon: Layers,
      color: 'from-indigo-500 to-purple-600',
      badge: 'Transparent Math',
      desc: 'Deterministic Road Condition Index (0-100) calculated using MoRTH engineering penalty formulas with zero opaque black-box AI scoring.',
      highlights: [
        'Mathematical proof transparency: Formula weights clearly displayed for inspectors',
        'Pothole depth severity weight (1.00) vs Fatigue cracking weight (0.85)',
        'Human-in-the-loop verification audit trail with cryptographic timestamps',
        'Standardized municipal cost estimation based on CPWD/PWD schedule of rates'
      ],
      actionText: 'View RCI Matrix',
      action: onOpenMatrix || onEnterDashboard
    },
    {
      id: 'tsp',
      title: 'Autonomous TSP 2-Opt Routing',
      subtitle: 'Repair Crew Optimization',
      icon: Navigation,
      color: 'from-rose-500 to-amber-600',
      badge: 'Graph-Theoretic',
      desc: 'Geodesic Traveling Salesperson tour optimization minimizing crew transit distance, municipal fuel burn, and traffic disruption across defect clusters.',
      highlights: [
        '2-Opt heuristic optimization generating optimal sequential stop order',
        'Distance and turnaround time reduction compared to naive FIFO repair visits',
        'Direct automated work order generation with crew dispatch assignments',
        'Interactive sequence timeline and GPX navigation waypoint export'
      ],
      actionText: 'Inspect Crew Tour',
      action: onOpenRoutes || onEnterDashboard
    },
    {
      id: 'copilot',
      title: 'Groq AI Infrastructure Copilot',
      subtitle: 'Grounded in SQL Evidence',
      icon: Bot,
      color: 'from-amber-500 to-orange-600',
      badge: 'Sub-150ms Groq LPU',
      desc: 'Conversational civil engineering assistant strictly grounded in database inspection records, defect coordinates, and municipal rate books.',
      highlights: [
        'Strict database grounding with 0 hallucination on inspection metrics',
        'Instant answers to budget inquiries, highest priority defects, and crew schedules',
        'Groq LPU hardware acceleration ensuring lightning-fast conversational response',
        'One-click prompt suggestions tailored for road inspectors and municipal executives'
      ],
      actionText: 'Chat with Copilot',
      action: onOpenCopilot || onEnterDashboard
    }
  ];

  const currentTab = featureTabs.find(t => t.id === activeFeatureTab) || featureTabs[0];
  const CurrentIcon = currentTab.icon;

  const distressTaxonomy = [
    { name: 'Pothole', code: 'D40', severity: 'Critical (P1)', weight: '1.00', repair: 'Full-Depth Cold/Hot Asphalt Patching', color: 'border-rose-300 bg-rose-50/50 text-rose-950' },
    { name: 'Alligator Crack', code: 'D00', severity: 'High (P2)', weight: '0.85', repair: 'Milling & Structural Overlay Resurfacing', color: 'border-orange-300 bg-orange-50/50 text-orange-950' },
    { name: 'Transverse Crack', code: 'D10', severity: 'Medium (P3)', weight: '0.65', repair: 'Polymer-Modified Bitumen Crack Sealing', color: 'border-yellow-300 bg-yellow-50/50 text-yellow-950' },
    { name: 'Longitudinal Crack', code: 'D20', severity: 'Medium (P3)', weight: '0.60', repair: 'Routing & Rubberized Asphalt Joint Fill', color: 'border-sky-300 bg-sky-50/50 text-sky-950' },
    { name: 'Other Distress', code: 'D44', severity: 'Low (P4)', weight: '0.50', repair: 'Surface Dressing & Micro-Surfacing Layer', color: 'border-emerald-300 bg-emerald-50/50 text-emerald-950' }
  ];

  return (
    <div className="min-h-screen bg-[#fafbfc] text-slate-900 flex flex-col font-sans selection:bg-sky-500/20 selection:text-sky-900 animate-fade-in-up">
      
      {/* Top Banner */}
      <div className="bg-slate-900 text-slate-200 text-xs py-2 px-4 sm:px-8 flex flex-wrap items-center justify-between gap-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-semibold text-slate-300">
            Government of India • MoRTH / NHAI Standard Road Infrastructure Intelligence
          </span>
          <span className="hidden md:inline-block px-2 py-0.5 rounded text-[10px] bg-sky-900/80 text-sky-200 font-mono font-bold border border-sky-700/50">
            PARAKRAM 1.0
          </span>
        </div>
        <div className="flex items-center gap-4 text-[11px] text-slate-400">
          <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-amber-400" /> Groq LPU Accelerated</span>
          <span className="flex items-center gap-1"><ShieldCheck className="w-3 h-3 text-emerald-400" /> 100% Real CV Inference</span>
        </div>
      </div>

      {/* Main Header / Navigation */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-8 py-3.5 flex items-center justify-between shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center shadow-md hover:scale-105 transition-transform">
            <Shield className="w-5 h-5 text-sky-400" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base tracking-tight text-slate-900">ROADSense AI</span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-extrabold bg-sky-50 text-sky-700 border border-sky-200">
                ENTERPRISE
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Autonomous Road Infrastructure Intelligence Platform</p>
          </div>
        </div>

        {/* Quick Actions in Navbar */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => onRunSampleDemo('pothole_video')}
            className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 text-xs font-bold transition-all shadow-2xs hover-lift cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <span>Judge 1-Click Demo</span>
          </button>
          
          <button
            onClick={onEnterDashboard}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-black text-white text-xs font-bold transition-all shadow-md hover-lift flex items-center gap-2 cursor-pointer"
          >
            <span>Launch Mission Control</span>
            <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-16 px-4 sm:px-8 max-w-7xl mx-auto w-full">
        {/* Subtle Background Glow Elements */}
        <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-gradient-to-tr from-sky-200/40 via-indigo-200/30 to-transparent blur-3xl -z-10 pointer-events-none rounded-full" />

        <div className="text-center space-y-5 max-w-4xl mx-auto">
          
          {/* Floating Pill Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/90 border border-sky-200/80 text-sky-900 text-xs font-bold shadow-2xs backdrop-blur-xs hover-lift">
            <span className="w-2 h-2 rounded-full bg-sky-500 animate-ping" />
            <Zap className="w-3.5 h-3.5 text-sky-600" />
            <span>Autonomous Pavement Distress & Infrastructure Intelligence</span>
          </div>

          {/* Main Hero Headline */}
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-slate-950 tracking-tight leading-[1.12]">
            Transform Dashcam Video into <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-sky-600 via-indigo-600 to-sky-800">
              Actionable Road Infrastructure AI
            </span>
          </h1>

          {/* Subtitle Description */}
          <p className="text-sm sm:text-base text-slate-600 leading-relaxed max-w-2xl mx-auto font-normal">
            Autonomous end-to-end road network surveillance powered by fine-tuned YOLOv8 vision, deterministic MoRTH RCI ratings, 3-layer GIS mapping, TSP 2-Opt repair crew routing, and Groq-accelerated AI Copilot.
          </p>

          {/* Primary Action Button Group */}
          <div className="flex flex-wrap items-center justify-center gap-3.5 pt-4">
            <button
              onClick={onEnterDashboard}
              className="px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-black text-white text-xs sm:text-sm font-bold shadow-lg hover:shadow-xl transition-all flex items-center gap-2.5 group hover-lift cursor-pointer"
            >
              <Activity className="w-4 h-4 text-sky-400 group-hover:rotate-12 transition-transform" />
              <span>Launch Mission Control</span>
              <ArrowRight className="w-4 h-4 text-sky-400 group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={() => onRunSampleDemo('pothole_video')}
              className="px-5 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-xs sm:text-sm font-bold shadow-md hover:shadow-lg transition-all flex items-center gap-2 hover-lift cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>Evaluate Built-in Rural Road Demo</span>
            </button>

            <button
              onClick={() => onRunCleanDemo('clean_road')}
              className="px-5 py-3.5 rounded-xl bg-white hover:bg-emerald-50/60 text-emerald-900 border border-emerald-300 text-xs sm:text-sm font-bold shadow-2xs hover:shadow-md transition-all flex items-center gap-2 hover-lift cursor-pointer"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Zero-Defect Clean Road Test</span>
            </button>
          </div>
        </div>

        {/* Dynamic Interactive Feature Spotlight Tabs */}
        <div className="mt-14 max-w-5xl mx-auto space-y-4">
          
          {/* Feature Navigation Pills */}
          <div className="flex flex-wrap items-center justify-center gap-2 p-1.5 bg-slate-100/80 rounded-2xl border border-slate-200/80 max-w-4xl mx-auto shadow-inner">
            {featureTabs.map(tab => {
              const TabIcon = tab.icon;
              const isActive = activeFeatureTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveFeatureTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    isActive 
                      ? 'bg-white text-slate-900 shadow-md border border-slate-200/60 scale-[1.02]' 
                      : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                  }`}
                >
                  <TabIcon className={`w-3.5 h-3.5 ${isActive ? 'text-sky-600' : 'text-slate-400'}`} />
                  <span>{tab.title}</span>
                </button>
              );
            })}
          </div>

          {/* Active Feature Interactive Showcase Card */}
          <div className="light-card rounded-2xl p-6 sm:p-8 bg-white border border-slate-200 shadow-lg hover-lift">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              
              {/* Left Column: Feature Details */}
              <div className="lg:col-span-7 space-y-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center shadow-xs">
                    <CurrentIcon className="w-5 h-5 text-sky-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-slate-900">{currentTab.title}</h3>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-sky-50 text-sky-800 border border-sky-200">
                        {currentTab.badge}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 font-medium">{currentTab.subtitle}</p>
                  </div>
                </div>

                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  {currentTab.desc}
                </p>

                {/* Highlights List */}
                <div className="space-y-2 pt-1">
                  {currentTab.highlights.map((h, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-slate-700">
                      <div className="w-4 h-4 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5 font-bold">
                        <Check className="w-2.5 h-2.5" />
                      </div>
                      <span>{h}</span>
                    </div>
                  ))}
                </div>

                {/* Action Link */}
                <div className="pt-2">
                  <button
                    onClick={currentTab.action}
                    className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-black text-white text-xs font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer hover-lift"
                  >
                    <span>{currentTab.actionText}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                  </button>
                </div>
              </div>

              {/* Right Column: Visual Architecture Preview Box */}
              <div className="lg:col-span-5 bg-gradient-to-br from-slate-900 to-slate-950 rounded-2xl p-5 text-slate-200 border border-slate-800 shadow-inner space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                  <span className="text-[11px] font-bold text-sky-400">ENGINE STATUS // ACTIVE</span>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[10px] text-slate-400">PARAKRAM 1.0</span>
                  </div>
                </div>

                <div className="space-y-2 text-[11px]">
                  <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50 flex items-center justify-between">
                    <span className="text-slate-400">Pipeline Stage</span>
                    <span className="text-sky-300 font-bold">{currentTab.title}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50 flex items-center justify-between">
                    <span className="text-slate-400">Standard</span>
                    <span className="text-emerald-300 font-bold">MoRTH IRC:SP:16</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50 flex items-center justify-between">
                    <span className="text-slate-400">Verification</span>
                    <span className="text-amber-300 font-bold">SHA-256 Audit Trail</span>
                  </div>
                </div>

                <div className="pt-1 text-[10px] text-slate-500">
                  Directly integrated into the Live Mission Control dashboard. Click to launch.
                </div>
              </div>

            </div>
          </div>
        </div>

      </section>

      {/* Distress Classification Taxonomy Grid (RDD2022 Standard) */}
      <section className="py-12 px-4 sm:px-8 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="text-center space-y-1.5 max-w-2xl mx-auto">
            <span className="text-xs font-bold text-sky-700 uppercase tracking-wider">Classification Taxonomy</span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
              RDD2022 Multi-Class Distress Detection
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              Calibrated severity formulas and localized municipal repair procedures.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 pt-2">
            {distressTaxonomy.map((item, idx) => (
              <div 
                key={idx}
                className={`p-4 rounded-xl border ${item.color} shadow-2xs hover-lift transition-all flex flex-col justify-between space-y-3`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold px-1.5 py-0.5 rounded bg-white/80 border border-slate-200">
                      {item.code}
                    </span>
                    <span className="text-[10px] font-extrabold tracking-tight">
                      Weight: {item.weight}
                    </span>
                  </div>
                  <h4 className="font-extrabold text-sm text-slate-900">{item.name}</h4>
                  <div className="text-[11px] font-semibold text-slate-700">
                    Severity: <b>{item.severity}</b>
                  </div>
                </div>

                <div className="text-[10px] text-slate-600 bg-white/70 p-2 rounded-lg border border-slate-200/60">
                  <span className="font-bold block text-slate-800">Action:</span>
                  {item.repair}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4-Step Interactive Flow Pipeline */}
      <section className="py-14 px-4 sm:px-8 max-w-7xl mx-auto w-full space-y-8">
        <div className="text-center space-y-1.5">
          <span className="text-xs font-bold text-sky-700 uppercase tracking-wider">Execution Pipeline</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">How RoadSense AI Operates</h2>
          <p className="text-xs text-slate-500">Continuous 4-stage pipeline from raw dashcam ingest to dispatched municipal work orders.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-2xs space-y-2.5 hover-lift">
            <div className="w-9 h-9 rounded-xl bg-sky-100 text-sky-800 font-bold flex items-center justify-center text-sm shadow-2xs">1</div>
            <h4 className="text-sm font-bold text-slate-900">Ingest Video & Telemetry</h4>
            <p className="text-xs text-slate-600 leading-relaxed">Dashcam container verification, automatic GPS telemetry extraction or GPX track synchronization.</p>
          </div>

          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-2xs space-y-2.5 hover-lift">
            <div className="w-9 h-9 rounded-xl bg-indigo-100 text-indigo-800 font-bold flex items-center justify-center text-sm shadow-2xs">2</div>
            <h4 className="text-sm font-bold text-slate-900">YOLOv8 & ByteTrack</h4>
            <p className="text-xs text-slate-600 leading-relaxed">Laplacian QA filter, 5-class distress inference, Kalman-filtered spatial deduplication.</p>
          </div>

          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-2xs space-y-2.5 hover-lift">
            <div className="w-9 h-9 rounded-xl bg-amber-100 text-amber-800 font-bold flex items-center justify-center text-sm shadow-2xs">3</div>
            <h4 className="text-sm font-bold text-slate-900">Deterministic RCI & GIS</h4>
            <p className="text-xs text-slate-600 leading-relaxed">Deterministic pavement health index, unit repair costing, and satellite map coordinate pinning.</p>
          </div>

          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-2xs space-y-2.5 hover-lift">
            <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm shadow-2xs">4</div>
            <h4 className="text-sm font-bold text-slate-900">Crew Tour & Copilot</h4>
            <p className="text-xs text-slate-600 leading-relaxed">Optimal 2-Opt repair sequence, municipal work orders, and grounded Groq AI intelligence.</p>
          </div>

        </div>
      </section>

      {/* Call to Action Card */}
      <section className="px-4 sm:px-8 pb-14 max-w-7xl mx-auto w-full">
        <div className="bg-gradient-to-r from-slate-900 via-slate-950 to-slate-900 rounded-3xl p-8 sm:p-10 text-white shadow-xl flex flex-col md:flex-row items-center justify-between gap-6 border border-slate-800">
          <div className="space-y-2 max-w-xl text-center md:text-left">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-900/80 text-sky-300 text-xs font-bold border border-sky-700/50">
              <Sparkles className="w-3.5 h-3.5" /> Ready for Live Road Evaluation
            </div>
            <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Ready to Inspect Highway Corridors?
            </h3>
            <p className="text-xs sm:text-sm text-slate-400">
              Launch the interactive Mission Control dashboard, explore real GIS defect maps, seek through dual synchronized dashcam video, or chat with the AI Copilot.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={onEnterDashboard}
              className="px-6 py-3.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 text-xs sm:text-sm font-bold shadow-lg hover:shadow-xl transition-all flex items-center gap-2 hover-lift cursor-pointer"
            >
              <span>Launch Mission Control</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onRunSampleDemo('pothole_video')}
              className="px-5 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs sm:text-sm font-bold border border-slate-700 transition-all flex items-center gap-2 hover-lift cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>1-Click Sample Demo</span>
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto bg-slate-900 text-slate-400 py-6 px-4 sm:px-8 border-t border-slate-800 text-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-sky-400" />
          <span className="text-slate-200 font-bold">ROADSense AI Platform</span>
          <span>• Production Evaluation Edition 2026</span>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={onEnterDashboard} className="hover:text-white font-semibold transition-colors cursor-pointer">Mission Control</button>
          <button onClick={onOpenGis || onEnterDashboard} className="hover:text-white font-semibold transition-colors cursor-pointer">GIS Center</button>
          <button onClick={onOpenStudio || onEnterDashboard} className="hover:text-white font-semibold transition-colors cursor-pointer">CV Studio</button>
          <button onClick={onOpenCopilot || onEnterDashboard} className="hover:text-white font-semibold transition-colors cursor-pointer">Groq Copilot</button>
        </div>
      </footer>

    </div>
  );
}
