import { Outlet, NavLink, Link } from "react-router-dom";
import github from "../../assets/github.svg";
import styles from "./Layout.module.css";

import utoLogo from '../../img/utp_logo.svg';

const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                {/* <div className={styles.headerContainer}> */}
                    <div className={styles.headerImg}>
                        <img src={utoLogo} alt="Logo UTP" />
                    </div>
                    <div className={styles.headerTitle}>
                        <div className={styles.headerTitlePrimary}>
                            <p className={styles.headerTitlePrimaryText}>
                                Asistente Virtual
                            </p>
                            <div className={styles.headerTitlePrimaryTag}>
                                <p>Proyecto con IA </p>
                            </div>
                        </div>
                        <p className={styles.headerTitleSecondary}>
                            Fundamentos de contabilidad y finanzas
                        </p>
                    </div>
                    <div className={styles.headerClear}>
                        {/* <p>Limpiar Chat</p> */}
                    </div>
                    {/* <Link to="/" className={styles.headerTitleContainer}>
                        <h3 className={styles.headerTitle}>Asistente del curso <strong>Fundamentos de Contabilidad y Finanzas</strong></h3>
                    </Link>
                    <h4 className={styles.headerRightText}>Información Indexada</h4> */}
                {/* </div> */}
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
