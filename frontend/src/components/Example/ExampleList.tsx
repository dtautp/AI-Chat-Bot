import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    {
        text: "¿Qué actividades debo realizar en la semana 13?",
        value: "¿Qué actividades debo realizar en la semana 13?"
    },
    { 
        text: "¿Cómo se define un activo?", 
        value: "¿Cómo se define un activo?" },
    { 
        text: "Elabora una tabla comparativa entre los conceptos de la semana 8", 
        value: "Elabora una tabla comparativa entre los conceptos de la semana 8" 
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {EXAMPLES.map((x, i) => (
                <li key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
