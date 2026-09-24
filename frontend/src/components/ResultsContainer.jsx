{/* frontend/src/components/ResultsContainer.jsx */}
export default function ResultsContainer({ loading, items }) {
  if (loading) {
    return (
      <div className="w-full max-w-2xl space-y-3">
        <div className="animate-pulse h-5 bg-neutral/DEFAULT rounded" />
        <div className="animate-pulse h-24 bg-neutral/DEFAULT rounded" />
      </div>
    );
  }

  if (!items?.length) {
    return (
      <p className="text-sm text-gray-500 text-center">
        No hay resultados todavía. Realiza una consulta para comenzar.
      </p>
    );
  }

  return <div className="space-y-4">{items}</div>;
}
