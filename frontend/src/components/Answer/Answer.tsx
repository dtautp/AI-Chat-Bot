import React, { useMemo, useState, useRef } from "react";
import { Stack, IconButton } from "@fluentui/react";
import DOMPurify from "dompurify";

import styles from "./Answer.module.css";

import { AskResponse, getCitationFilePath } from "../../api";
import { parseAnswerToHtml } from "./AnswerParser";
import { AnswerIcon } from "./AnswerIcon";

import playAudio from '../../img/play-audio.svg';
import pauseAudio from '../../img/pause-audio.svg';

interface Props {
    answer: AskResponse;
    isSelected?: boolean;
    onCitationClicked: (filePath: string) => void;
    onThoughtProcessClicked: () => void;
    onSupportingContentClicked: () => void;
    onFollowupQuestionClicked?: (question: string) => void;
    showFollowupQuestions?: boolean;
}

export const Answer = ({
    answer,
    isSelected,
    onCitationClicked,
    onThoughtProcessClicked,
    onSupportingContentClicked,
    onFollowupQuestionClicked,
    showFollowupQuestions
}: Props) => {
    const parsedAnswer = useMemo(() => parseAnswerToHtml(answer.answer, onCitationClicked), [answer]);

    const sanitizedAnswerHtml = DOMPurify.sanitize(parsedAnswer.answerHtml);
    
    const [speechText, setSpeechText] = useState<string>('');
    const [isSpeaking, setIsSpeaking] = useState<boolean>(false); 
    const synth = useRef<SpeechSynthesis | null>(null);
    const utterance = useRef<SpeechSynthesisUtterance | null>(null);

    // Función para reproducir el texto usando la síntesis de voz
    const reproducirTexto = (texto: string) => {
        if (synth.current && synth.current.speaking) {
            synth.current.cancel(); // Cancelar la reproducción actual antes de iniciar una nueva
        }
        
        utterance.current = new SpeechSynthesisUtterance(texto);
        utterance.current.lang = 'es-ES'; // Configurar el idioma a español
        synth.current = window.speechSynthesis;
        synth.current.speak(utterance.current);

        setIsSpeaking(true);
    };

    // Función para detener la reproducción
    const detenerReproduccion = () => {
        if (synth.current && synth.current.speaking) {
            synth.current.cancel();
            setIsSpeaking(false);
        }
    };

    // Escuchar eventos para actualizar el estado cuando la reproducción termina
    React.useEffect(() => {
        if (utterance.current) {
            utterance.current.onend = () => setIsSpeaking(false);
            utterance.current.onerror = () => setIsSpeaking(false);
        }
    }, [utterance.current]);

    // Actualizar el estado de speechText cuando answer.answer cambie
    React.useEffect(() => {
        setSpeechText(answer.answer || '');
    }, [answer.answer]);
    
    // Manejador de clic en el botón
    const handleClick = () => {
        if (isSpeaking) {
            detenerReproduccion();
        } else {
            reproducirTexto(speechText);
        }
    };

    return (
        <Stack className={`${styles.answerContainer} ${isSelected && styles.selected}`} verticalAlign="space-between">
            {/* <Stack.Item>
                <Stack horizontal horizontalAlign="space-between">
                    <AnswerIcon />
                    <div>
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: "Lightbulb" }}
                            title="Show thought process"
                            ariaLabel="Show thought process"
                            onClick={() => onThoughtProcessClicked()}
                            disabled={!answer.thoughts}
                        />
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: "ClipboardList" }}
                            title="Show supporting content"
                            ariaLabel="Show supporting content"
                            onClick={() => onSupportingContentClicked()}
                            disabled={!answer.data_points.length}
                        />
                    </div>
                </Stack>
            </Stack.Item> */}

            <Stack.Item grow>
                <div className={styles.answerText} dangerouslySetInnerHTML={{ __html: sanitizedAnswerHtml }}></div>
                <button className={styles.audioPlayButton} onClick={handleClick}>
                    <img src={isSpeaking ? pauseAudio : playAudio} alt={isSpeaking ? 'Pause' : 'Play'} />
                    <p>{isSpeaking ? 'Detener' : 'Escuchar'}</p>
                </button>
            </Stack.Item>

            {/*!!parsedAnswer.citations.length && (
                <Stack.Item>
                    <Stack horizontal wrap tokens={{ childrenGap: 5 }}>
                        <span className={styles.citationLearnMore}>Citations:</span>
                        {parsedAnswer.citations.map((x, i) => {
                            const path = getCitationFilePath(x);
                            return (
                                <a key={i} className={styles.citation} title={x} onClick={() => onCitationClicked(path)}>
                                    {`${++i}. ${x}`}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )

            !!parsedAnswer.followupQuestions.length && showFollowupQuestions && onFollowupQuestionClicked && (
                <Stack.Item>
                    <Stack horizontal wrap className={`${!!parsedAnswer.citations.length ? styles.followupQuestionsList : ""}`} tokens={{ childrenGap: 6 }}>
                        <span className={styles.followupQuestionLearnMore}>Follow-up questions:</span>
                        {parsedAnswer.followupQuestions.map((x, i) => {
                            return (
                                <a key={i} className={styles.followupQuestion} title={x} onClick={() => onFollowupQuestionClicked(x)}>
                                    {`${x}`}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )*/}
        </Stack>
    );
};
