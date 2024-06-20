import { useState, useEffect } from "react";
import { Stack, TextField } from "@fluentui/react";
import { Send28Filled } from "@fluentui/react-icons";

import styles from "./QuestionInput.module.css";

import uploadFiles from '../../img/paperclip.svg';
import microphone from '../../img/microphone.svg'

// Define webkitSpeechRecognition for TypeScript
declare global {
    interface Window {
        webkitSpeechRecognition: any;
    }
}

// Define types for SpeechRecognition events
interface SpeechRecognitionEvent {
    results: SpeechRecognitionResultList;
    error: string;
}

interface Props {
    onSend: (question: string) => void;
    disabled: boolean;
    placeholder?: string;
    clearOnSend?: boolean;
}

export const QuestionInput = ({ onSend, disabled, placeholder, clearOnSend }: Props) => {
    const [question, setQuestion] = useState<string>("");
    const [listening, setListening] = useState<boolean>(false);
    const [isRecognitionComplete, setIsRecognitionComplete] = useState<boolean>(false);

    useEffect(() => {
        if (!('webkitSpeechRecognition' in window)) {
            alert("Tu navegador no soporta el reconocimiento de voz. Prueba con Google Chrome.");
        }
    }, []);

    useEffect(() => {
        if (isRecognitionComplete) {
            sendQuestion();
            setIsRecognitionComplete(false);
        }
    }, [isRecognitionComplete]);

    const sendQuestion = () => {
        if (disabled || !question.trim()) {
            return;
        }

        onSend(question);

        if (clearOnSend) {
            setQuestion("");
        }
    };

    const onEnterPress = (ev: React.KeyboardEvent<Element>) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            sendQuestion();
        }
    };

    const onQuestionChange = (_ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        if (!newValue) {
            setQuestion("");
        } else if (newValue.length <= 1000) {
            setQuestion(newValue);
        }
    };

    const sendQuestionDisabled = disabled || !question.trim();

    const UploadFilesClick = () => {
        alert('Lo siento, aún no contamos con esta función 😔');
        // Aquí puedes realizar cualquier otra acción que desees al hacer clic en la imagen
    };

    const ActivateMicro = () => {

        if (!('webkitSpeechRecognition' in window)) {
            alert("Tu navegador no soporta el reconocimiento de voz. Prueba con Google Chrome.");
            return;
        }

        const reconocimiento = new window.webkitSpeechRecognition();
        reconocimiento.lang = "es-ES"; // Configurar el idioma a español
        reconocimiento.continuous = false;
        reconocimiento.interimResults = false;

        reconocimiento.onstart = function() {
            setListening(true);
        };

        reconocimiento.onresult = function(event: SpeechRecognitionEvent) {
            const resultado = event.results[0][0].transcript;
            setQuestion(resultado);
            setListening(false);
            setIsRecognitionComplete(true); // Set recognition complete flag to true
        };

        reconocimiento.onerror = function(event: SpeechRecognitionEvent) {
            alert("Error: " + event.error);
            setListening(false);
        };

        reconocimiento.onend = function() {
            setListening(false);
        };

        reconocimiento.start();
    };

    return (
        <Stack horizontal className={styles.questionInputContainer}>
            <div className={styles.chatInputText}>
                <img src={uploadFiles} alt="Clip Adjuntar Archivo" className={styles.chatUploadFolder} onClick={UploadFilesClick}/>
                <TextField
                    className={styles.questionInputTextArea}
                    placeholder={placeholder}
                    multiline
                    resizable={false}
                    borderless
                    value={question}
                    onChange={onQuestionChange}
                    onKeyDown={onEnterPress}
                />
                <img
                    src={microphone}
                    alt="Activar micrófono"
                    className={`${styles.chatMicrophone} ${listening ? styles.chatMicrophoneDisabled : ""}`}
                    onClick={!listening ? ActivateMicro : undefined}
                />
                {/* <button onClick={ActivateMicro} disabled={listening}>Micrófono</button> */}
            </div>
            
            <div className={styles.questionInputButtonsContainer}>
                <div
                    className={`${styles.questionInputSendButton} ${sendQuestionDisabled ? styles.questionInputSendButtonDisabled : ""}`}
                    aria-label="Ask question button"
                    onClick={sendQuestion}
                >
                    <Send28Filled primaryFill="rgba(255, 255, 255, 1)" />
                    <p className={styles.questionInputSendButtonText} >Enviar</p>
                </div>
                
            </div>
        </Stack>
    );
};
