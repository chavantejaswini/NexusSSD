interface PagePlaceholderProps {
  title: string;
  description: string;
  phase: string;
}

export function PagePlaceholder({ title, description, phase }: PagePlaceholderProps) {
  return (
    <section>
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="mt-2 max-w-2xl text-slate-400">{description}</p>
      <div className="mt-6 rounded-lg border border-dashed border-white/15 bg-nexus-panel/50 p-8 text-slate-500">
        Coming in {phase}.
      </div>
    </section>
  );
}
