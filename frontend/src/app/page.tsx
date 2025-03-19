// pages/page.tsx
"use client";

import Link from "next/link";
import styles from "./page.module.css";

export default function Page() {
  return (
    <div className={styles.page}>
      <h1 className="text-2xl font-bold">메인 페이지</h1>
      <nav className={styles.nav}>
        <ul>
          <li><Link href="/Home">🏠 홈</Link></li>
        </ul>
      </nav>
      <footer className={styles.footer}>© 2025 OlLama Chatbot. All rights reserved.</footer>
    </div>
  );
}