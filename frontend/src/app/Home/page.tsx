"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";
import Chat from "@/components/Chat";
import List from "@/components/List";

export default function Home() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [todayData, setTodayData] = useState<any[]>([]);  // ✅ 오늘 날짜 데이터 상태 추가

  const fetchTodayData = async () => {
    try {
      const response = await fetch("http://localhost:7000/today");
      const rawData = await response.json();
      
      // ✅ 데이터 문자열을 객체 형태로 변환
      const processedData = rawData.map((entry: string) => {
        return Object.fromEntries(entry.split(", ").map((pair: string) => pair.split(": ")));
      });
      
      setTodayData(processedData);
    } catch (error) {
      console.error("❌ 데이터를 불러오는 중 오류 발생:", error);
    }
  };

  useEffect(() => {
    fetchTodayData();
  }, []);

  return (
    
    <div className={styles.page}>

      <div className={`${styles.sidebar} ${isSidebarOpen ? styles.open : ""}`}>
        <button className={styles.sidebarToggle} onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
          {isSidebarOpen ? "⬅" : "📄"}
        </button>
        {isSidebarOpen && (
          <div className={styles.fileList}>
            <List />
          </div>
        )}
      </div>

      {/* 메인 섹션 */}
      <div className={styles.main}>
        <div id="chat" className="mt-8 w-full">
          {/* ✅ Chat에서 그래프 데이터를 받을 수 있도록 prop 추가 */}
          <Chat />
        </div>
      </div>

      <div className={styles.todayDataContainer}>
        <h2 className="text-xl font-bold">📊 오늘의 데이터</h2>
        {todayData.length > 0 ? (
          <table className={styles.dataTable}>
            <thead>
              <tr>
                {Object.keys(todayData[0]).map((key) => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {todayData.map((item, index) => (
                <tr key={index}>
                  {Object.keys(todayData[0]).map((key) => (
                    <td key={key}>{item[key] ?? ""}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>📅 오늘 날짜의 데이터가 없습니다.</p>
        )}
      </div>


      {/* 푸터 */}
      <footer className={styles.footer}>
        © 2025 OlLama Chatbot. All rights reserved.
      </footer>
    </div>
  );
}
