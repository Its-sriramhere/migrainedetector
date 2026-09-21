import { Hero } from "../components/landing/Hero";
import { TrustStats } from "../components/landing/TrustStats";
import { Problem } from "../components/landing/Problem";
import { DataFlow } from "../components/landing/DataFlow";
import { Personalization } from "../components/landing/Personalization";
import { IoTMonitoring } from "../components/landing/IoTMonitoring";
import { AIPrediction } from "../components/landing/AIPrediction";
import { ExplainableAI } from "../components/landing/ExplainableAI";
import { DashboardPreview } from "../components/landing/DashboardPreview";
import { DemoSection } from "../components/landing/DemoSection";
import { Research } from "../components/landing/Research";
import { CTA } from "../components/landing/CTA";

export function HomePage() {
  return (
    <>
      <Hero />
      <TrustStats />
      <Problem />
      <DataFlow />
      <Personalization />
      <IoTMonitoring />
      <AIPrediction />
      <ExplainableAI />
      <DashboardPreview />
      <DemoSection />
      <Research />
      <CTA />
    </>
  );
}