"use client";

import Link from "next/link";
import styles from "./page.module.css";

export default function Page() {
  return (
    <div className={styles.page}>
      <h1 className={styles.title}>메인 페이지</h1>
      
      <nav className={styles.nav}>
        <ul className={styles.cardGrid}>
          <li className={styles.card}>
            <Link href="/Home">
              <div>
                <h2>🏠 챗봇</h2>
                <p>챗봇에게 질문하세요</p>
              </div>
            </Link>
          </li>
          <li className={styles.card}>
            <Link href="/Monitering">
              <div>
                <h2>📊 모니터링</h2>
                <p>실시간 데이터와 로그 확인</p>
              </div>
            </Link>
          </li>
        </ul>
      </nav>

      <footer className={styles.footer}>
        © 2025 OlLama Chatbot. All rights reserved.
      </footer>
    </div>
  );
}
