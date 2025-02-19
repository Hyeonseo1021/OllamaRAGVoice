import styles from "./page.module.css";
import Chat from "@/components/Chat";

export default function Home() {
  return (
    <div className={styles.page}>
      {/* 메인 섹션 */}
      <div className={styles.main}>
        <h1>🗣️ 올라마 챗봇</h1>

        {/* Chat 컴포넌트 */}
        <div id="chat" className="mt-8 w-full">
          <Chat />
        </div>
      </div>

      {/* 푸터 */}
      <footer className={styles.footer}>
        © 2025 Olama Chatbot. All rights reserved.
      </footer>
    </div>
  );
}
