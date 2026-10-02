"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card } from "./card";
import { cn } from "../../lib/utils";
import { useNavigate } from "react-router-dom";

interface FeatureItem {
  title: string;
  alt?: string;
  content: string | React.ReactNode;
  href?: string;
}

function FeatureMedia({
  content,
  alt,
}: {
  content: string | React.ReactNode;
  alt?: string;
}) {
  if (typeof content !== "string") {
    return <div className="w-full h-full">{content}</div>;
  }

  const isVideo = /\.(mp4|webm|ogg)$/i.test(content);
  const isImage =
    /\.(jpg|jpeg|png|webp|gif|avif|svg)$/i.test(content) ||
    /unsplash|images\./i.test(content);

  if (isVideo) {
    return (
      <video
        src={content}
        autoPlay
        muted
        loop
        playsInline
        className="w-full h-full object-cover"
      />
    );
  }

  if (isImage) {
    return (
      <img src={content} alt={alt} className="w-full h-full object-cover" />
    );
  }

  return (
    <div className="flex items-center justify-center w-full h-full p-8">
      <p className="text-sm text-muted-foreground leading-relaxed">{content}</p>
    </div>
  );
}

const items: FeatureItem[] = [
  {
    title: "Overview",
    alt: "View your candidate intelligence overview and system health.",
    content: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&q=80&w=1000",
    href: "/"
  },
  {
    title: "Upload",
    alt: "Upload candidate resumes for instant AI-powered parsing and analysis.",
    content: "https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&q=80&w=1000",
    href: "/upload"
  },
  {
    title: "Jobs",
    alt: "Manage your active job postings and recruitment pipelines.",
    content: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1000",
    href: "/jobs"
  },
  {
    title: "Talent Explorer",
    alt: "Browse and filter through your entire indexed candidate database.",
    content: "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&q=80&w=1000",
    href: "/explorer"
  },
  {
    title: "Candidate Portal",
    alt: "Access detailed candidate profiles, semantic matching scores, and insights.",
    content: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&q=80&w=1000",
    href: "/candidate"
  },
  {
    title: "Analytics",
    alt: "Deep dive into recruitment metrics, AI processing stats, and team performance.",
    content: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1000",
    href: "/analytics"
  }
];

export default function FeaturesWithPanel() {
  const [active, setActive] = React.useState(0);
  const navigate = useNavigate();

  return (
    <section className="relative w-full py-16">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 lg:gap-16 lg:items-start">
          <div>
            <h2 className="text-4xl font-bold tracking-tight text-[#FFF7EE] md:text-5xl lg:text-6xl mb-10">
              Platform Features.
            </h2>

            <ul className="flex flex-col gap-1">
              {items.map((item, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, y: 8 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{
                    duration: 0.35,
                    delay: index * 0.07,
                    ease: "easeOut",
                  }}
                  onMouseEnter={() => setActive(index)}
                  onClick={() => item.href && navigate(item.href)}
                  className={cn(
                    "flex flex-col px-4 py-3.5 rounded-xl cursor-pointer transition-all duration-200 lg:flex-row lg:items-center lg:gap-4 group hover:scale-[1.02]",
                    active === index
                      ? "bg-[rgba(58,44,110,0.45)] border border-[rgba(251,230,184,0.16)]"
                      : "border border-transparent hover:bg-[rgba(58,44,110,0.2)]",
                  )}
                >
                  <div className="flex flex-row items-center gap-4 w-full lg:contents">
                    <span
                      className={cn(
                        "size-7 rounded-full flex items-center justify-center text-xs font-medium shrink-0 transition-colors duration-200",
                        active === index
                          ? "bg-gradient-to-br from-[#C4749B] to-[#F6B98A] text-[#140F25] shadow-[0_0_12px_rgba(246,185,138,0.30)]"
                          : "bg-[rgba(255,247,238,0.1)] text-[rgba(255,247,238,0.5)] group-hover:bg-[rgba(255,247,238,0.2)]",
                      )}
                    >
                      {index + 1}
                    </span>
                    <div className="flex flex-col">
                      <span
                        className={cn(
                          "text-sm font-semibold transition-colors duration-200",
                          active === index
                            ? "text-[#FFF7EE]"
                            : "text-[rgba(255,247,238,0.65)] group-hover:text-[rgba(255,247,238,0.9)]",
                        )}
                      >
                        {item.title}
                      </span>
                      {active === index && item.alt && (
                        <motion.span 
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="text-[12px] text-[rgba(255,247,238,0.55)] mt-1 lg:hidden"
                        >
                          {item.alt}
                        </motion.span>
                      )}
                    </div>
                  </div>

                  <AnimatePresence initial={false}>
                    {active === index && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
                        className="w-full overflow-hidden lg:hidden"
                      >
                        <Card className="w-full mt-3 overflow-hidden p-0 gap-0 aspect-[4/3] relative border-0 bg-transparent rounded-xl shadow-[0_10px_30px_rgba(20,10,40,0.5)]">
                          <div className="absolute inset-0">
                            <FeatureMedia
                              content={item.content}
                              alt={item.alt}
                            />
                          </div>
                        </Card>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.li>
              ))}
            </ul>
          </div>

          <div className="hidden lg:flex flex-col sticky top-24">
            <motion.div
               whileHover={{ scale: 1.02 }}
               transition={{ type: "spring", stiffness: 400, damping: 30 }}
            >
              <Card 
                className="relative w-full aspect-[4/3] overflow-hidden p-0 gap-0 border border-[rgba(251,230,184,0.16)] rounded-2xl bg-[rgba(58,44,110,0.45)] shadow-[0_20px_40px_rgba(20,10,40,0.5)] cursor-pointer"
                onClick={() => items[active].href && navigate(items[active].href)}
              >
                <AnimatePresence mode="wait">
                  <motion.div
                    key={active}
                    initial={{ opacity: 0, y: 12, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.98 }}
                    transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
                    className="absolute inset-0"
                  >
                    <FeatureMedia
                      content={items[active].content}
                      alt={items[active].alt}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[rgba(58,44,110,0.8)] to-transparent pointer-events-none" />
                    <div className="absolute bottom-6 left-6 right-6 pointer-events-none">
                      <h3 className="text-[#FBE6B8] font-bold text-xl mb-2 flex items-center gap-2">
                        {items[active].title}
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                      </h3>
                      <p className="text-[rgba(255,247,238,0.7)] text-sm leading-relaxed">{items[active].alt}</p>
                    </div>
                  </motion.div>
                </AnimatePresence>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
