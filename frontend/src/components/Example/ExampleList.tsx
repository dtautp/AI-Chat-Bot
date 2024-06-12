import { Example } from "./Example";

import styles from "./Example.module.css";

import bolt from '../../img/bolt.svg';
import book from '../../img/book.svg';
import filePen from '../../img/file-pen.svg';
import question from '../../img/question.svg';

export type ExampleModel = {
    text: string;
    value: string;
    img: string;
};

const EXAMPLES: ExampleModel[] = [
    {
        text: "¿Cómo se define un activo?",
        value: "¿Cómo se define un activo?",
        img: book
    },
    { 
        text: "¿Qué debo de considerar pra sacar 20 en mi Tarea - Tarea Académica 2 (TA2)?", 
        value: "¿Qué debo de considerar pra sacar 20 en mi Tarea - Tarea Académica 2 (TA2)?",
        img: filePen
    },
    { 
        text: "¿Qué actividades debo realizar en la semana 13?", 
        value: "¿Qué actividades debo realizar en la semana 13?",
        img: question
    },
    { 
        text: "Elabora una tabla comparativa entre los conceptos de la semana 8", 
        value: "Elabora una tabla comparativa entre los conceptos de la semana 8",
        img: bolt
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
                    <Example text={x.text} value={x.value} img={x.img} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
