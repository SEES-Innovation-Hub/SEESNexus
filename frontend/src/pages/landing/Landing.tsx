import { usePrefetchAuthPages } from "../../hooks/usePrefetchAuthPages";
import { HeroSection } from "./HeroSection";
import { JoinSection } from "./JoinSection";
import { LandingFooter } from "./LandingFooter";
import { LandingNav } from "./LandingNav";
import { PillarsSection } from "./PillarsSection";
import { ProjectShowcaseRail } from "./ProjectShowcaseRail";
import { TeamSection } from "./TeamSection";

export function Landing() {
  usePrefetchAuthPages();

  return (
    <div className="flex min-h-screen flex-col">
      <LandingNav />
      <main className="flex-1">
        <HeroSection />
        <ProjectShowcaseRail />
        <PillarsSection />
        <TeamSection />
        <JoinSection />
      </main>
      <LandingFooter />
    </div>
  );
}
