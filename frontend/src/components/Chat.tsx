"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import styles from "../styles/Chat.module.css";

export default function Chat({ onGraphGenerated }: { onGraphGenerated?: (graphData: string) => void }) {
  const [messages, setMessages] = useState<{ role: string; content: string; graph?: string }[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState<any | null>(null);
  const [useRAG, setUseRAG] = useState(false);
  const [hasMessages, setHasMessages] = useState(false);
  const [file, setFile] = useState<File | null>(null); // ✅ 파일 상태 추가
  const [isUploading, setIsUploading] = useState(false); // ✅ 파일 업로드 상태

  useEffect(() => {
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition =
        (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recog = new SpeechRecognition();
      recog.lang = "ko-KR";
      recog.interimResults = false;

      recog.onstart = () => setIsListening(true);
      recog.onend = () => setIsListening(false);
      recog.onresult = (event: any) => setInput(event.results[0][0].transcript);

      setRecognition(recog);
    } else {
      console.error("Speech Recognition API not supported in this browser.");
    }
  }, []);

  const speak = (text: string) => {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "ko-KR";
      window.speechSynthesis.speak(utterance);
    } else {
      console.error("Speech Synthesis API not supported in this browser.");
    }
  };

  // ✅ 메시지 전송 함수
  const sendMessage = async () => {
    if (!input.trim()) return;

    if (!hasMessages) setHasMessages(true);

    const newMessages = [...messages, { role: "user", content: input }];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post("http://localhost:7000/chat", {
        message: input,
        use_rag: useRAG
      });

      if (response.data.graph) {
        setMessages([
          ...newMessages,
          { role: "assistant", content: response.data.response, graph: response.data.graph }
        ]);

        // ✅ 그래프 데이터를 부모(Home.tsx)로 전달하여 표시
        if (onGraphGenerated) {
          onGraphGenerated(response.data.graph);
        }
      } else {
        setMessages([
          ...newMessages,
          { role: "assistant", content: response.data.response }
        ]);
      }

      speak(response.data.response);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // ✅ STT 시작 함수
  const startListening = () => {
    if (recognition) {
      recognition.start();
    } else {
      console.error("STT is not initialized.");
    }
  };

  // ✅ 파일 업로드 함수 (유지)
  const uploadFile = async () => {
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:7000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      alert(response.data.message);
      setFile(null);
    } catch (error) {
      console.error("파일 업로드 오류:", error);
    } finally {
      setIsUploading(false);
    }
  };

  useEffect(() => {
    if (file) {
      uploadFile();
    }
  }, [file]);

  return (
    <div className={`${styles.chatContainer} ${hasMessages ? styles.chatActive : ""}`}>
      <div className={styles.chatHeader}>
          {!hasMessages && <h2>질문하세요</h2>}     
      </div>
      
      {/* 채팅 기록 표시 */}
      <div className={`${styles.chatHistory} ${hasMessages ? styles.chatActive : ""}`}>
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`${styles.message} ${
              msg.role === "user" ? styles.userMessage : styles.botMessage
            }`}
          >
            <strong>{msg.role === "user" ? "You" : "Bot"}:</strong> {msg.content}
            {/* ✅ CrewAI가 반환한 그래프가 있으면 자동 출력 */}
            {msg.graph && (
              <img
                src={`data:image/png;base64,${msg.graph}`}
                alt="Generated Graph"
                className={styles.graphImage}
              />
            )}
          </div>
        ))}
        {isLoading && <div className={styles.loadingMessage}>⏳ 응답 생성 중...</div>}
      </div>
        
      {/* 입력 및 버튼 영역 */}
      <div className={`${styles.inputContainer} ${hasMessages ? styles.inputFixed : styles.inputCenter}`}>
        {/* ✅ 파일 업로드 UI 유지 */}
        <div className={styles.uploadContainer}>
          <label htmlFor="file-upload" className={styles.fileLabel}>📂 파일 선택</label>
          <input
            id="file-upload"
            type="file"
            onChange={(e) => {
              const selectedFile = e.target.files?.[0] || null;
              setFile(selectedFile);
            }}
            className={styles.fileInput}
          />
          {isUploading && <p className={styles.uploadMessage}>⏳ 파일 업로드 중...</p>}
        </div>

        <input
          type="text"
          className={styles.inputBox}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder="Type a message..."
        />
        <button onClick={sendMessage} className={styles.sendButton} disabled={isLoading}>
          {isLoading ? "⌛" : "⬆"}
        </button>
        <button onClick={startListening} className={styles.sttButton} disabled={!recognition}>
          {isListening ? "Listening..." : "🎙️"}
        </button>
      </div>
    </div>
  );
}
