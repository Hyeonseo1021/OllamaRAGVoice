"use client";

import { useEffect, useState } from "react";
import styles from "./page.module.css";
import Chat from "@/components/Chat";
import List from "@/components/List"; // ✅ List 컴포넌트 추가

export default function Home() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [today, setToday] = useState<string>(""); 
  const [facilityData, setFacilityData] = useState<any>(null); 

  useEffect(() => {
    const date = new Date().toISOString().split("T")[0];
    setToday(date);

    const fetchFacilityData = async () => {
      try {
        const response = await fetch(`http://localhost:7000/files`);
        const data = await response.json();
        setFacilityData(data);
      } catch (error) {
        console.error("❌ 스마트팜 데이터 불러오는 중 오류 발생:", error);
      }
    };

    fetchFacilityData();
  }, []);

  return (
    <div className={styles.page}>
      <div className={`${styles.sidebar} ${isSidebarOpen ? styles.open : ""}`}>
        <button className={styles.sidebarToggle} onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
          {isSidebarOpen ? "⬅" : "📄"}
        </button>
        {isSidebarOpen && (
          <div className={styles.fileList}>
            <List /> {/* ✅ 파일 목록 컴포넌트 추가 */}
          </div>
        )}
      </div>
      {/* 메인 섹션 */}
      <div className={styles.main}>
        {/* Chat 컴포넌트 */}
        <div id="chat" className="mt-8 w-full">
          <Chat />
        </div>
      </div>

      {/* 푸터 */}
      <footer className={styles.footer}>
        © 2025 OlLama Chatbot. All rights reserved.
      </footer>
    </div>
  );
}
