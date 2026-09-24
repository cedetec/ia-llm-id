export const ResultsContext = createContext();

export const ResultsProvider = ({ children }) => {
  const [results, setResults] = useState([]);
  const [metrics, setMetrics] = useState({});
  return (
    <ResultsContext.Provider value={{ results, setResults, metrics, setMetrics }}>
      {children}
    </ResultsContext.Provider>
  );
};
