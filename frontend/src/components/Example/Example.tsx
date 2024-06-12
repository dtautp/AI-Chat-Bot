import styles from "./Example.module.css";

interface Props {
    text: string;
    value: string;
    img: string;
    onClick: (value: string) => void;
}

export const Example = ({ text, value, img, onClick }: Props) => {
    return (
        <div className={styles.example} onClick={() => onClick(value)}>
            <img src={img} />
            <p className={styles.exampleText}>{text}</p>
        </div>
    );
};
