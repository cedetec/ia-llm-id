export default function TagList({ onPick }) {
  const tags = [
    { label: "Objetivo", q: "¿Cuál es el objetivo del concurso InES Género 2025?" },
    { label: "Fechas", q: "¿Cuáles son las fechas de postulación de InES Género 2025?" },
    { label: "Montos", q: "¿Cuál es el monto de financiamiento de InES Género 2025?" },
  ];

  return (
    <div className="flex gap-2 flex-wrap">
      {tags.map((t) => (
        <button
          key={t.label}
          onClick={() => onPick?.(t.q)}
          className="text-sm bg-secondary text-white px-3 py-1 rounded-full hover:bg-secondary-dark"
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
