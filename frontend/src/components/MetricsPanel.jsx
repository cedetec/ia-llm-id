<Card className="p-4">
  <h4 className="text-md font-semibold mb-2">Estadísticas del Asistente</h4>
  <ul className="text-sm text-gray-600">
    <li>Total de consultas: {totalConsultas}</li>
    <li>Tiempo promedio de respuesta: {tiempoPromedio}s</li>
    <li>Precisión semántica: {precision}%</li>
  </ul>
  {/* Aquí puedes añadir un gráfico de barras o pastel con Recharts */}
</Card>
