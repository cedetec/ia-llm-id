{/* frontend/src/pages/ResultsPage.jsx */}
import ResultsView from "../components/ResultsView";

export default function ResultsPage({
    data
}){

    return(

        <ResultsView
            respuesta={data?.respuesta}
            documento={data?.documento}
            modelo={data?.modelo}
            tiempo={data?.tiempo}
            chunks={data?.chunks}
            tokens={data?.tokens}
            score={data?.score}
        />

    );

}
