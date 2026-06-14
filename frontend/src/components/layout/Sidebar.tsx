import { useEffect, useState } from "react";

interface SidebarLink {
  id: string;
  label: string;
}

interface Props {
  links: SidebarLink[];
  /** ID of the active section, or null to derive automatically. */
  activeId?: string | null;
}

/** Sticky in-page navigation for long results pages. Highlights the section in view. */
export default function Sidebar({ links, activeId }: Props) {
  const [autoActive, setAutoActive] = useState<string>(links[0]?.id ?? "");

  useEffect(() => {
    if (activeId !== undefined) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]) setAutoActive(visible[0].target.id);
      },
      { rootMargin: "-30% 0px -55% 0px", threshold: [0, 0.25, 0.5, 0.75, 1] },
    );
    links.forEach((l) => {
      const el = document.getElementById(l.id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [links, activeId]);

  const current = activeId ?? autoActive;

  return (
    <aside className="hidden lg:block sticky top-20 self-start w-52 shrink-0">
      <nav aria-label="Section navigation" className="space-y-1 text-sm">
        {links.map((l) => (
          <a
            key={l.id}
            href={`#${l.id}`}
            className={[
              "block px-3 py-1.5 rounded-md transition-colors border-l-2",
              current === l.id
                ? "border-accent text-accent bg-accent/10"
                : "border-transparent text-muted hover:text-fg hover:bg-white/5",
            ].join(" ")}
          >
            {l.label}
          </a>
        ))}
      </nav>
    </aside>
  );
}
