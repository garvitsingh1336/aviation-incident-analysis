/** Minimal monochrome stroke icons (currentColor). */
const P = {
  overview: "M3 3h7v7H3zM14 3h7v4h-7zM14 10h7v11h-7zM3 14h7v7H3z",
  topics: "M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5",
  clusters: "M6 7a2 2 0 100-4 2 2 0 000 4zM18 9a2 2 0 100-4 2 2 0 000 4zM9 18a2 2 0 100-4 2 2 0 000 4zM17 19a2 2 0 100-4 2 2 0 000 4z",
  factors: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  relationships: "M6 12a3 3 0 100-6 3 3 0 000 6zM18 8a3 3 0 100-6 3 3 0 000 6zM18 20a3 3 0 100-6 3 3 0 000 6zM8.5 10.5l7-3M8.7 13l6.6 4",
  trends: "M3 17l6-6 4 4 8-8M21 7v5M21 7h-5",
  entities: "M20.6 13.4L13 21a2 2 0 01-3 0l-7-7a2 2 0 010-3l7.6-7.6A2 2 0 0111.4 3H19a2 2 0 012 2v7.6a2 2 0 01-.4 0.8zM7.5 8.5h.01",
  search: "M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3",
  reports: "M4 4h16v16H4zM4 9h16M4 14h16M9 4v16",
  sun: "M12 17a5 5 0 100-10 5 5 0 000 10zM12 1v3M12 20v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M1 12h3M20 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1",
  moon: "M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z",
  close: "M18 6L6 18M6 6l12 12",
  chevron: "M9 18l6-6-6-6",
  refresh: "M21 12a9 9 0 11-3-6.7M21 3v5h-5",
  external: "M14 3h7v7M21 3l-9 9M10 5H5a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2v-5",
};

export default function Icon({ name, size = 18, stroke = 1.7, fill = false, style }) {
  const d = P[name] || "";
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={fill ? "currentColor" : "none"}
      stroke={fill ? "none" : "currentColor"}
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={style}
      aria-hidden="true"
    >
      <path d={d} />
    </svg>
  );
}
