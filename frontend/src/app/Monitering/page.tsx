// pages/page.tsx
"use client";

import Link from "next/link";
import styles from "./page.module.css";

export default function Page() {
  return (
    <div className={styles.page}>
      <div className={styles.topRightNav}>
        <Link href="/" className={styles.homeLink}>🏠 홈으로</Link>
      </div>
      <h1 className="text-2xl font-bold">모니터링</h1>
      <nav className={styles.nav}>
        <ul>
          
          
        </ul>
      </nav>
      <footer className={styles.footer}>© 2025 OlLama Chatbot. All rights reserved.</footer>
    </div>
  );
}