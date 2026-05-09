import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Search, Briefcase, Building2, Plane, ShieldCheck, CheckCircle } from 'lucide-react';

import img1 from "../imports/ws-chae--jVX4mW1Uac-unsplash.jpg";
import img2 from "../imports/yeonhee-VWLhifg5VMA-unsplash.jpg";
import img3 from "../imports/clary-garcia-QHlGCk9I_lY-unsplash.jpg";
import img4 from "../imports/ji-seongkwang-CX7fI2LXJgo-unsplash.jpg";

const unsplash5 = "https://images.unsplash.com/photo-1633272266667-6ab973d9427a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzZW91bCUyMGNpdHklMjBtb2Rlcm4lMjBhcmNoaXRlY3R1cmV8ZW58MXx8fHwxNzc3ODcxMTgxfDA&ixlib=rb-4.1.0&q=80&w=1080";

const allImages = [img1, img2, img3, img4, unsplash5];

export default function Landing() {
  const [bgImageIndex, setBgImageIndex] = useState(0);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const providedImages = [img1, img2, img3, img4];
    const randomIndex = Math.floor(Math.random() * providedImages.length);
    const selectedImage = providedImages[randomIndex];
    
    const indexInAll = allImages.indexOf(selectedImage);
    setBgImageIndex(indexInAll);
    setIsLoaded(true);
  }, []);

  if (!isLoaded) return null;

  const sectionImages = allImages.filter((_, i) => i !== bgImageIndex);

  return (
    <div className="font-sans text-neutral-900 bg-[#fcfaf5] min-h-screen selection:bg-[#0EA37B] selection:text-white">
       <HeroSection bgImage={allImages[bgImageIndex]} />
       <BrandHero image={sectionImages[0]} />
       <FeatureSection />
       <AboutMeSection image1={sectionImages[1]} image2={sectionImages[2]} />
       <Footer />
    </div>
  );
}

const LogoSVG = () => (
  <div className="flex items-center gap-3 cursor-pointer group">
    <svg className="w-12 h-12 md:w-16 md:h-16 transition-transform duration-700 ease-out group-hover:-translate-y-1" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
          <clipPath id="p39clip"><circle cx="60" cy="60" r="54"/></clipPath>
          <linearGradient id="p39sky" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#F4EDDC"/>
              <stop offset="60%" stopColor="#FFB8A8"/>
              <stop offset="100%" stopColor="#FF6B5B"/>
          </linearGradient>
          <linearGradient id="p39sea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0EA37B"/>
              <stop offset="100%" stopColor="#085E48"/>
          </linearGradient>
      </defs>
      <g clipPath="url(#p39clip)">
          <rect x="0" y="0" width="120" height="72" fill="url(#p39sky)"/>
          <g className="transition-transform duration-700 group-hover:-translate-y-2">
              <circle cx="60" cy="62" r="18" fill="#F4EDDC"/>
              <circle cx="60" cy="62" r="18" fill="#FF6B5B" opacity="0.85"/>
          </g>
          <path d="M -4,78 L 22,54 L 40,70 L 58,44 L 82,72 L 102,58 L 128,78 L 128,120 L -4,120 Z" fill="#085E48" opacity="0.35"/>
          <rect x="0" y="72" width="120" height="48" fill="url(#p39sea)"/>
          <g stroke="#F4EDDC" strokeWidth="1.2" fill="none" opacity="0.55" strokeLinecap="round">
              <path d="M 10,84 Q 30,80 50,84 T 90,84 T 130,84"/>
              <path d="M 0,94 Q 22,90 44,94 T 86,94 T 130,94"/>
              <path d="M 12,104 Q 34,100 56,104 T 98,104 T 140,104"/>
          </g>
      </g>
      <circle cx="60" cy="60" r="54" fill="none" stroke="#085E48" strokeWidth="2"/>
    </svg>
    <div className="flex flex-col items-start">
       <span className="font-serif text-3xl md:text-4xl tracking-tight font-medium text-white flex items-baseline gap-1">
         <span>Paradiso</span>
       </span>
       <span className="text-[10px] md:text-xs text-white/70 tracking-widest uppercase font-semibold hidden sm:block">
         대한민국 39가지 체류자격, 하나의 플랫폼으로
       </span>
    </div>
  </div>
);

function HeroSection({ bgImage }: { bgImage: string }) {
  return (
    <div className="relative min-h-screen w-full flex flex-col overflow-hidden bg-black pt-8 pb-16">
      <div className="absolute inset-0">
        <motion.img 
          key={bgImage}
          initial={{ scale: 1.05, opacity: 0.8 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          src={bgImage} 
          className="w-full h-full object-cover opacity-80" 
          alt="Background" 
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-black/60 mix-blend-multiply"></div>
      </div>
      
      <nav className="relative z-10 w-full px-6 md:px-12 flex flex-col md:flex-row justify-between items-center text-white gap-6 md:gap-0">
        <LogoSVG />
        <div className="flex gap-4">
          <button className="px-6 py-2.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white hover:text-black transition-all font-bold text-sm shadow-lg">
            로그인
          </button>
        </div>
      </nav>

      <div className="relative z-10 px-6 md:px-12 py-12 md:py-20 flex flex-col items-center justify-center flex-1 max-w-6xl w-full mx-auto text-center">
        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.15] mb-12 drop-shadow-2xl"
        >
          대한민국 39가지<br />체류자격을 한 번에
        </motion.h1>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="w-full max-w-2xl bg-white/15 backdrop-blur-2xl border border-white/30 p-2 pl-6 rounded-2xl md:rounded-full flex items-center shadow-2xl focus-within:bg-white/25 focus-within:border-white/50 transition-all"
        >
          <Search className="w-6 h-6 text-white/70 mr-3 flex-shrink-0" />
          <input 
            type="text" 
            placeholder="비자 코드 및 키워드 직접 검색 (예: 유학, 취업, F-2)" 
            className="flex-1 bg-transparent border-none outline-none text-white placeholder-white/60 text-base md:text-lg w-full"
          />
          <button className="bg-[#0EA37B] hover:bg-[#085E48] text-white px-6 md:px-10 py-3.5 rounded-xl md:rounded-full font-bold transition-colors ml-2 shadow-lg whitespace-nowrap">
            검색
          </button>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="mt-12 flex w-full max-w-3xl"
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full">
            <button className="flex flex-col items-center justify-center gap-3 bg-white/10 backdrop-blur-md border border-white/20 p-5 rounded-2xl hover:bg-[#0EA37B]/40 hover:border-[#0EA37B] text-white transition-all group shadow-lg">
              <Briefcase className="w-7 h-7 group-hover:scale-110 transition-transform text-white/80 group-hover:text-white" />
              <span className="text-xs md:text-sm font-bold text-white/90 group-hover:text-white text-center leading-tight">취업신고용<br/>업종/직종 코드</span>
            </button>
            <button className="flex flex-col items-center justify-center gap-3 bg-white/10 backdrop-blur-md border border-white/20 p-5 rounded-2xl hover:bg-[#0EA37B]/40 hover:border-[#0EA37B] text-white transition-all group shadow-lg">
              <Building2 className="w-7 h-7 group-hover:scale-110 transition-transform text-white/80 group-hover:text-white" />
              <span className="text-xs md:text-sm font-bold text-white/90 group-hover:text-white text-center leading-tight">관할 출입국<br/>관서 조회</span>
            </button>
            <button className="flex flex-col items-center justify-center gap-3 bg-white/10 backdrop-blur-md border border-white/20 p-5 rounded-2xl hover:bg-white/20 hover:border-white text-white transition-all group shadow-lg">
              <Plane className="w-7 h-7 group-hover:scale-110 transition-transform text-white/80 group-hover:text-white" />
              <span className="text-xs md:text-sm font-bold text-white/90 group-hover:text-white text-center leading-tight">입국 전<br/>사증 발급</span>
            </button>
            <button className="flex flex-col items-center justify-center gap-3 bg-white/10 backdrop-blur-md border border-white/20 p-5 rounded-2xl hover:bg-white/20 hover:border-white text-white transition-all group shadow-lg">
              <ShieldCheck className="w-7 h-7 group-hover:scale-110 transition-transform text-white/80 group-hover:text-white" />
              <span className="text-xs md:text-sm font-bold text-white/90 group-hover:text-white text-center leading-tight">입국 후<br/>체류 관리</span>
            </button>
          </div>
        </motion.div>
      </div>

      <motion.button 
        onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
        animate={{ y: [0, 8, 0] }}
        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/60 hover:text-white transition-colors cursor-pointer p-2 z-20 bg-transparent border-none"
        aria-label="아래로 스크롤"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </motion.button>
    </div>
  );
}

function BrandHero({ image }: { image: string }) {
  return (
    <section className="relative py-24 md:py-32 flex flex-col items-center bg-gradient-to-br from-[#5b7ea6] via-[#7aaa8a] to-[#2d6a8f] text-center px-6 z-10">
      <div className="absolute inset-0 z-0">
        <img src={image} className="w-full h-full object-cover opacity-20 mix-blend-overlay" alt="Brand Background" />
      </div>
      <div className="relative z-10 flex flex-col items-center gap-6 max-w-4xl">
        <motion.h2 
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          className="text-4xl md:text-[3.5rem] font-extrabold text-white leading-[1.2] tracking-tight drop-shadow-lg"
        >
          분절된 체류 행정,<br />단일 플랫폼으로 통합하다.
        </motion.h2>
        <p className="text-lg md:text-xl text-white/90 tracking-wider uppercase font-bold">
          Korea's 39 visa categories. Unified.
        </p>
        <div className="flex flex-wrap justify-center gap-4 mt-6">
          <button className="px-8 py-3.5 bg-white text-gray-900 rounded-xl font-bold hover:-translate-y-1 hover:shadow-xl transition-all flex items-center gap-2">
            서비스 소개 <span className="text-xs text-gray-500 font-bold ml-1">ABOUT</span>
          </button>
          <button className="px-8 py-3.5 bg-transparent border-2 border-white/60 text-white rounded-xl font-bold hover:bg-white/10 hover:border-white hover:-translate-y-1 transition-all flex items-center gap-2">
            1345 직접 문의 <span className="text-xs text-white/80 font-bold ml-1">1345 HOTLINE</span>
          </button>
        </div>
      </div>

      <div className="relative z-20 mt-16 md:mt-24 w-full max-w-5xl bg-white/95 backdrop-blur-md rounded-[32px] shadow-2xl p-6 md:p-10 grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-0 divide-y md:divide-y-0 md:divide-x divide-gray-200 translate-y-0 md:translate-y-1/2">
        <StatCard icon="💼" num="14" label="취업·전문직" en="Employment" tags={["D-7", "D-8", "E-7", "E-9"]} />
        <StatCard icon="🎓" num="8" label="유학·연수" en="Study" tags={["D-2", "D-4", "D-10"]} />
        <StatCard icon="🏠" num="7" label="거주·결혼" en="Residence" tags={["F-2", "F-4", "F-5", "F-6"]} />
        <StatCard icon="✈️" num="10" label="방문·기타" en="Visit & Other" tags={["B-2", "C-3", "H-2"]} />
      </div>
    </section>
  );
}

function StatCard({ icon, num, label, en, tags }: any) {
  return (
    <motion.div whileHover={{ y: -5 }} className="flex flex-col items-center text-center p-4 py-6 md:py-4">
      <div className="text-4xl mb-3">{icon}</div>
      <div className="text-5xl font-extrabold text-[#FF6B5B] mb-2 tracking-tight">{num}</div>
      <div className="text-base font-extrabold text-gray-900 leading-tight">
        {label}
        <span className="block text-xs text-gray-500 font-bold mt-1 uppercase tracking-wider">{en}</span>
      </div>
      <div className="flex flex-wrap justify-center gap-1.5 mt-4">
        {tags.map((t: string) => (
          <span key={t} className="px-2.5 py-1 bg-gray-100 border border-gray-200 text-gray-600 rounded-full text-xs font-bold">{t}</span>
        ))}
      </div>
    </motion.div>
  );
}

function FeatureSection() {
  return (
    <section className="pt-16 md:pt-48 pb-24 px-6 max-w-7xl mx-auto">
      <div className="bg-white/70 backdrop-blur-xl rounded-[32px] border border-[#D8CAB0] p-8 md:p-16 grid grid-cols-1 lg:grid-cols-2 gap-12 md:gap-20 items-center shadow-lg">
        <motion.div initial={{ opacity: 0, x: -20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}>
          <h2 className="text-3xl md:text-5xl font-extrabold leading-tight text-gray-900 mb-4 tracking-tight">
            법무부 출입국·외국인정책본부<br />매뉴얼 기반
          </h2>
          <p className="text-sm font-bold text-gray-500 tracking-wider uppercase mb-6">
            Built on Ministry of Justice Immigration Manual
          </p>
          <p className="text-lg text-gray-600 leading-relaxed mb-8 font-medium">
            본 서비스는 2026년 현행 출입국관리법 시행규칙과 출입국·외국인정책본부 실무 매뉴얼을 기반으로 합니다. 다만 최종 판단은 관할 출입국·외국인관서에 귀속됩니다.
          </p>
          <button className="px-6 py-3.5 bg-gray-900 text-white rounded-xl font-bold hover:bg-black transition-all flex items-center gap-2 shadow-lg hover:shadow-xl">
            1345 외국인종합안내센터 <span className="text-xs text-gray-400 font-bold ml-1 tracking-wider uppercase">Contact 1345</span>
          </button>
        </motion.div>
        
        <motion.div initial={{ opacity: 0, x: 20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="bg-gradient-to-br from-[#b2ede4] to-[#7dd3e8] rounded-3xl p-6 md:p-8 shadow-xl">
           <ul className="space-y-4">
             {[
               { ko: "39개 체류자격 통합 검색", en: "Search across 39 visa types" },
               { ko: "자격별 구비서류 자동 생성", en: "Auto-generated document checklist" },
               { ko: "관할 출입국관서 즉시 조회", en: "Find your jurisdiction office" },
               { ko: "취업신고 직종·업종 코드", en: "Employment notification codes" }
             ].map((item, i) => (
               <li key={i} className="flex items-center gap-4 bg-white/90 backdrop-blur-sm p-4 md:p-5 rounded-2xl shadow-sm hover:scale-[1.02] transition-transform">
                 <div className="w-10 h-10 shrink-0 bg-[#0EA37B] rounded-full flex items-center justify-center text-white font-bold shadow-md">
                   <CheckCircle className="w-6 h-6" />
                 </div>
                 <div>
                   <strong className="block text-gray-900 text-lg font-extrabold">{item.ko}</strong>
                   <span className="text-xs text-gray-500 font-bold uppercase tracking-wider mt-0.5 block">{item.en}</span>
                 </div>
               </li>
             ))}
           </ul>
        </motion.div>
      </div>
    </section>
  );
}

function AboutMeSection({ image1, image2 }: { image1: string, image2: string }) {
  return (
    <section className="py-24 px-6 max-w-7xl mx-auto space-y-24 md:space-y-32">
      <div className="text-center">
        <motion.h2 initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight">
          플랫폼 소개
        </motion.h2>
      </div>

      <div className="bg-gradient-to-br from-[#FFB8A8]/30 to-transparent border border-[#D8CAB0] rounded-[32px] shadow-sm p-8 md:p-12 grid grid-cols-1 lg:grid-cols-[1fr_1.5fr] gap-12 md:gap-16 items-center">
        <div className="flex flex-col items-center gap-12 bg-white/60 backdrop-blur-md rounded-3xl p-8 py-16 shadow-inner border border-white/50">
          <Anagram />
        </div>

        <div className="space-y-6">
          <h3 className="text-2xl font-extrabold text-gray-900 flex items-center flex-wrap gap-2">
            브랜드 철학 및 어원 
            <span className="text-sm text-gray-500 font-bold uppercase tracking-widest ml-1">— Brand Philosophy & Etymology</span>
          </h3>
          <ul className="space-y-5">
             <li className="relative pl-5 text-gray-700 leading-relaxed font-medium">
               <span className="absolute left-0 top-0 text-[#FF6B5B] font-extrabold text-xl">·</span>
               <strong className="text-gray-900 font-extrabold mr-1">Paradiso</strong> 
               — 이탈리아어 "낙원(Paradise)". 한국에서의 체류가 모두에게 낙원처럼 머무를 만한 곳이기를 바랍니다.
             </li>
             <li className="relative pl-5 text-gray-700 leading-relaxed font-medium">
               <span className="absolute left-0 top-0 text-[#FF6B5B] font-extrabold text-xl">·</span>
               <strong className="text-gray-900 font-extrabold mr-1">Diaspora (애너그램)</strong> 
               — 'Paradiso'는 이주민을 뜻하는 영단어 'Diaspora'의 알파벳 8개를 재배열(Anagram)한 단어입니다. 고국을 떠나온 이주민들이 대한민국에서 안정적인 정주 환경을 영위할 수 있도록 지원한다는 지향점을 담았습니다.
             </li>
          </ul>
          <div className="bg-[#0EA37B]/10 border-l-4 border-[#0EA37B] p-5 rounded-r-2xl mt-6">
             <p className="text-[#085E48] font-extrabold text-lg tracking-tight">300만 체류 외국인 시대를 위한 공식 인프라로의 도약.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 md:gap-20 items-center">
         <div className="rounded-[32px] overflow-hidden aspect-[4/3] shadow-2xl">
           <img src={image1} className="w-full h-full object-cover hover:scale-105 transition-transform duration-1000 ease-out" alt="Paradiso Start" />
         </div>
         <div className="space-y-6">
           <h3 className="text-3xl md:text-4xl font-extrabold text-gray-900 tracking-tight">Paradiso의 시작</h3>
           <p className="text-lg text-gray-600 leading-relaxed font-medium">
             대한민국에는 39가지의 체류자격이 존재하지만, 법령과 매뉴얼은 파편화되어 있어 진입 장벽이 높습니다. Paradiso는 출입국·외국인정책본부 실무 매뉴얼을 기반으로, 가장 정확한 비자 정보와 관할 관서를 단일 플랫폼에서 직관적으로 제공하기 위해 기획되었습니다. 향후 체류 외국인 300만 시대를 대비하는 공식 인프라로 도약하고자 합니다.
           </p>
         </div>
      </div>

      <div className="space-y-12">
        <div className="max-w-3xl">
          <h3 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-6 tracking-tight">핵심 가치 및 비전</h3>
          <p className="text-lg text-gray-600 font-medium leading-relaxed">단순한 정보 나열을 넘어, 사용자 맞춤형 AI 상황 분석과 정확한 직종·산업 코드 매칭을 통해 실질적인 행정 처리 시간을 단축하고 정보의 비대칭성을 해소합니다.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          <HobbyCard icon="📑" title="Data Integrity" desc="법무부 출입국·외국인정책본부 실무 매뉴얼과 시행규칙을 1차 출처로 삼습니다." bg="bg-gradient-to-br from-[#FFB8A8] to-[#7DD8B8]" />
          <HobbyCard icon="🧭" title="User Centric" desc="39개 자격을 4개 카테고리로 묶어 한 화면에서 비교·검색합니다." bg="bg-gradient-to-br from-[#e1eaec] to-[#f1ece2]" />
          <HobbyCard icon="✨" title="AI Powered" desc="국적·체류자격·직무 정보로 본인 상황에 맞는 절차를 즉시 제시합니다." bg="bg-gradient-to-tr from-[#f1ece2] to-[#7DD8B8]" />
        </div>
      </div>

      {/* Roadmap */}
      <div className="max-w-4xl border-t-2 border-[#D8CAB0]/50 pt-16">
         <h3 className="text-3xl font-extrabold text-gray-900 mb-10 tracking-tight">로드맵</h3>
         <div className="space-y-0">
           <RoadmapRow year="2026 Q3" title="정식 서비스 런칭 및 다국어 지원 확대" desc="영어·중국어·베트남어 UI 동시 제공, 1345 핫라인 연동 강화" />
           <RoadmapRow year="2026 Q1" title="AI 맞춤형 비자 진단 고도화" desc="RAG 기반 매뉴얼 검색·국적별 케이스 매칭으로 정밀도 향상" />
           <RoadmapRow year="2025 Q4" title="공공데이터 활용 공모전 출품 및 베타 테스트" desc="39개 자격 통합 검색 MVP 공개·실사용자 피드백 수집" />
         </div>
      </div>

      {/* Footer Hero */}
      <div className="mt-32 w-full h-[480px] md:h-[500px] rounded-[40px] overflow-hidden relative shadow-2xl flex flex-col items-center justify-center p-8 text-center bg-gray-900 group">
         <img src={image2} className="absolute inset-0 w-full h-full object-cover opacity-40 group-hover:scale-105 group-hover:opacity-30 transition-all duration-1000 ease-out" alt="Footer Hero" />
         <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/50 to-transparent"></div>
         <div className="relative z-10 flex flex-col items-center">
            <span className="text-[#7DD8B8] font-extrabold tracking-[0.25em] uppercase text-sm mb-6 drop-shadow-md">Paradiso</span>
            <h2 className="text-4xl md:text-6xl font-extrabold text-white leading-tight mb-10 drop-shadow-xl tracking-tight">
              대한민국 39가지<br />체류자격, 한 곳에서.
            </h2>
            <div className="flex flex-wrap justify-center gap-3">
              {["📑 매뉴얼 기반", "🤖 AI 분석", "🏛 관할관서 조회", "💼 직종·업종 코드"].map(c => (
                <span key={c} className="px-5 py-2.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-white font-bold text-sm shadow-lg">
                  {c}
                </span>
              ))}
            </div>
         </div>
      </div>
    </section>
  );
}

function HobbyCard({ icon, title, desc, bg }: any) {
  return (
    <div className={`p-8 rounded-[32px] shadow-lg flex flex-col justify-end aspect-square ${bg} relative overflow-hidden group hover:-translate-y-2 transition-transform duration-300`}>
      <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-300"></div>
      <div className="w-14 h-14 rounded-2xl bg-white/90 backdrop-blur-sm flex items-center justify-center text-3xl shadow-md mb-auto">
        {icon}
      </div>
      <h4 className="text-2xl font-extrabold text-[#085E48] mb-3 tracking-tight">{title}</h4>
      <p className="text-sm font-bold text-[#085E48]/80 leading-relaxed">{desc}</p>
    </div>
  )
}

function RoadmapRow({ year, title, desc }: any) {
  return (
    <div className="grid grid-cols-[auto_1fr_auto] gap-6 md:gap-8 items-center py-8 border-b border-[#D8CAB0]/50 group">
       <div className="w-3.5 h-3.5 rounded-full bg-[#FF6B5B] ring-4 ring-[#FFB8A8]/40 group-hover:scale-125 transition-transform duration-300 shadow-sm"></div>
       <div>
         <h4 className="text-xl font-extrabold text-gray-900 mb-2 tracking-tight">{title}</h4>
         <p className="text-gray-500 font-medium text-sm md:text-base">{desc}</p>
       </div>
       <div className="px-5 py-2 bg-gray-100 rounded-full border border-gray-200 text-gray-700 font-extrabold whitespace-nowrap shadow-sm text-sm">
         {year}
       </div>
    </div>
  )
}

function Anagram() {
  const stageRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const topRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const botRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [svgSize, setSvgSize] = useState({ w: 0, h: 0 });
  const [lineData, setLineData] = useState<{ x1: number; y1: number; x2: number; y2: number; len: number }[]>([]);

  // DIASPORA[i] maps to PARADISO position index
  const MAP = [4, 5, 1, 6, 0, 7, 2, 3];
  const topWord = ["D", "I", "A", "S", "P", "O", "R", "A"];
  const botWord = ["P", "A", "R", "A", "D", "I", "S", "O"];

  const buildLines = useCallback(() => {
    if (!stageRef.current) return;
    const sRect = stageRef.current.getBoundingClientRect();
    if (sRect.width === 0 || sRect.height === 0) return;

    const newLines = MAP.map((bIdx, tIdx) => {
      const tEl = topRefs.current[tIdx];
      const bEl = botRefs.current[bIdx];
      if (!tEl || !bEl) return null;
      const tR = tEl.getBoundingClientRect();
      const bR = bEl.getBoundingClientRect();
      const x1 = tR.left + tR.width / 2 - sRect.left;
      const y1 = tR.bottom - sRect.top + 3;
      const x2 = bR.left + bR.width / 2 - sRect.left;
      const y2 = bR.top - sRect.top - 3;
      const len = Math.hypot(x2 - x1, y2 - y1);
      return { x1, y1, x2, y2, len };
    }).filter(Boolean) as { x1: number; y1: number; x2: number; y2: number; len: number }[];

    setLineData(newLines);
    setSvgSize({ w: sRect.width, h: sRect.height });
  }, []);

  useEffect(() => {
    const timer = setTimeout(buildLines, 80);
    window.addEventListener('resize', buildLines);
    return () => { clearTimeout(timer); window.removeEventListener('resize', buildLines); };
  }, [buildLines]);

  // Cycle highlight animation
  useEffect(() => {
    let idx = -1;
    const interval = setInterval(() => {
      idx = (idx + 1) % 10;
      setActiveIndex(idx < 8 ? idx : -1);
    }, 600);
    return () => clearInterval(interval);
  }, []);

  // Re-trigger stroke animation key
  const [animKey, setAnimKey] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setAnimKey(k => k + 1), 3200);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="w-full max-w-xs md:max-w-sm select-none">
      {/* Label DIASPORA */}
      <div className="text-center mb-1">
        <span className="text-[10px] font-bold tracking-[0.18em] uppercase text-gray-400">DIASPORA</span>
      </div>

      {/* Stage: top row, SVG, bottom row */}
      <div ref={stageRef} className="relative" style={{ paddingTop: 8, paddingBottom: 8 }}>
        {/* Top row */}
        <div className="flex justify-center relative z-10">
          {topWord.map((char, i) => (
            <span
              key={`top-${i}`}
              ref={el => { topRefs.current[i] = el; }}
              style={{ width: '2em', textAlign: 'center', padding: '0.2em 0', letterSpacing: '0.1em' }}
              className={`inline-block font-extrabold text-xl md:text-2xl transition-all duration-250 cursor-default
                ${activeIndex === i
                  ? 'text-[#0EA37B] -translate-y-0.5 drop-shadow-[0_0_10px_rgba(14,163,123,0.45)]'
                  : 'text-[#085E48]'
                }`}
            >
              {char}
            </span>
          ))}
        </div>

        {/* SVG lines */}
        {svgSize.w > 0 && (
          <svg
            ref={svgRef}
            className="w-full pointer-events-none"
            style={{ display: 'block', height: 80, overflow: 'visible' }}
            viewBox={`0 0 ${svgSize.w} 80`}
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <marker id="ag-arr-active" markerWidth="6" markerHeight="6" refX="4.5" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0.5 L0,5.5 L4.5,3 z" fill="#0EA37B" />
              </marker>
              <marker id="ag-arr-dim" markerWidth="6" markerHeight="6" refX="4.5" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0.5 L0,5.5 L4.5,3 z" fill="#9ca3af" />
              </marker>
            </defs>
            {lineData.map((ln, i) => {
              const isActive = activeIndex === i;
              // Scale y coordinates from original stage height to SVG height (80)
              // The SVG represents a "bridge" between the two word rows
              const ySvgH = svgSize.h > 0 ? svgSize.h : 200;
              // lines go from top of SVG (0) to bottom (80) -- we scale y1,y2 relative to stage
              // Actually we need to re-map: the SVG sits BETWEEN the rows in the padded area
              // We'll just draw from top of SVG (0+offset) to bottom (80-offset)
              const x1 = ln.x1; const x2 = ln.x2;
              const y1 = 4; const y2 = 76;
              const len = Math.hypot(x2 - x1, y2 - y1);
              return (
                <line
                  key={`${animKey}-line-${i}`}
                  x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={isActive ? '#0EA37B' : '#9ca3af'}
                  strokeWidth={isActive ? 2.5 : 1.5}
                  strokeLinecap="round"
                  markerEnd={isActive ? 'url(#ag-arr-active)' : 'url(#ag-arr-dim)'}
                  opacity={isActive ? 1 : 0.45}
                  strokeDasharray={len}
                  strokeDashoffset={0}
                  style={{
                    transition: 'stroke 0.25s, stroke-width 0.25s, opacity 0.25s',
                    animation: `agDraw-${i} 0.38s cubic-bezier(0.85, 0, 0.15, 1) ${i * 45}ms both`,
                  }}
                />
              );
            })}
          </svg>
        )}

        {/* Spacer if SVG not built yet */}
        {svgSize.w === 0 && <div style={{ height: 80 }} />}

        {/* Bottom row */}
        <div className="flex justify-center relative z-10">
          {botWord.map((char, i) => {
            const srcIdx = MAP.indexOf(i);
            const isActive = activeIndex === srcIdx;
            return (
              <span
                key={`bot-${i}`}
                ref={el => { botRefs.current[i] = el; }}
                style={{ width: '2em', textAlign: 'center', padding: '0.2em 0', letterSpacing: '0.1em' }}
                className={`inline-block font-extrabold text-xl md:text-2xl transition-all duration-250 cursor-default
                  ${isActive
                    ? 'text-[#FF6B5B] translate-y-0.5 drop-shadow-[0_0_10px_rgba(255,107,91,0.45)]'
                    : 'text-[#E0513E]'
                  }`}
              >
                {char}
              </span>
            );
          })}
        </div>
      </div>

      {/* Label PARADISO */}
      <div className="text-center mt-1">
        <span className="text-[10px] font-bold tracking-[0.18em] uppercase text-gray-400">PARADISO</span>
      </div>

      {/* Keyframe style injection */}
      <style>{`
        ${Array.from({ length: 8 }, (_, i) => {
          const len = lineData[i] ? Math.hypot(lineData[i].x2 - lineData[i].x1, 76 - 4) : 80;
          return `
            @keyframes agDraw-${i} {
              from { stroke-dashoffset: ${len}; opacity: 0; }
              1% { opacity: 1; stroke-dashoffset: ${len}; }
              to { stroke-dashoffset: 0; opacity: 1; }
            }
          `;
        }).join('')}
      `}</style>
    </div>
  );
}

function Footer() {
  return (
    <footer className="py-16 px-6 md:px-12 flex flex-col items-center justify-center bg-white text-center border-t border-gray-200">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-gray-900 flex items-center justify-center text-[#0EA37B] font-serif font-bold text-xl shadow-md">
          P
        </div>
        <span className="font-serif text-2xl tracking-tight font-medium text-gray-900">Paradiso</span>
      </div>
      
      <div className="flex gap-8 text-gray-500 font-bold text-sm mb-8">
        <button className="hover:text-gray-900 transition-colors">Terms</button>
        <button className="hover:text-gray-900 transition-colors">Privacy</button>
        <button className="hover:text-gray-900 transition-colors">Contact</button>
      </div>

      <p className="text-gray-400 text-xs font-medium">© 2026 Paradiso. All rights reserved.</p>
    </footer>
  );
}