import { useState } from "react";
import ImageGenerator from "../../components/ImageGenerator";

// TEMPORARY, dev-only sandbox (route is compiled out of production builds) so
// ImageGenerator can be tried before the project form that will host it exists.
// Delete once Emmanuel's create/edit project form uses the component.
export function ImageGeneratorPreview() {
  const [savedUrl, setSavedUrl] = useState<string | null>(null);

  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="w-full max-w-md space-y-6 rounded-2xl border border-sees-teal/40 bg-gradient-card p-8 shadow-sees-card">
        <h1 className="text-2xl font-semibold text-sees-mint">
          Image generator (dev preview)
        </h1>
        <ImageGenerator defaultTopic="Smart irrigation controller" onUploaded={setSavedUrl} />
        {savedUrl && (
          <div className="space-y-2 text-sm text-white/70">
            <p>
              Saved as the thumbnail URL: <span className="break-all font-mono text-sees-mint">{savedUrl}</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
