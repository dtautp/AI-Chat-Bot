import styles from "./UserChatMessage.module.css";

interface Props {
    message: string;
}

export const UserChatMessage = ({ message }: Props) => {
    return (
        <div className={styles.container}>
            <div className={styles.message}>
                <p>{message}</p>
            </div>
        </div>
    );
};
