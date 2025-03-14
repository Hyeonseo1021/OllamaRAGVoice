"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import styles from "../styles/Chat.module.css";

export default function Chat() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false); // STT 상태
  const [recognition, setRecognition] = useState<any | null>(null); // STT 객체 상태
  const [file, setFile] = useState<File | null>(null); // 파일 상태
  const [isUploading, setIsUploading] = useState(false);
  const [useRAG, setUseRAG] = useState(false); // ✅ RAG 버튼 상태 추가
  const [hasMessages, setHasMessages] = useState(false); // 채팅 시작 여부 상태 추가

  // ✅ STT 초기화 (Web Speech API)
  useEffect(() => {
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition =
        (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recog = new SpeechRecognition();
      recog.lang = "ko-KR";
      recog.interimResults = false;

      recog.onstart = () => setIsListening(true);
      recog.onend = () => setIsListening(false);
      recog.onresult = (event: any) => setInput(event.results[0][0].transcript); // STT 결과

      setRecognition(recog);
    } else {
      console.error("Speech Recognition API not supported in this browser.");
    }
  }, []);

  // ✅ TTS (Text-to-Speech) 함수
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

      const updatedMessages = [
        ...newMessages,
        { role: "assistant", content: response.data.response },
      ];
      setMessages(updatedMessages);
      speak(response.data.response); // TTS로 챗봇 응답 읽어주기
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

  // ✅ 파일 상태가 업데이트되면 자동 업로드 실행
  useEffect(() => {
    if (file) {
      uploadFile();
    }
  }, [file]);

  // ✅ 파일 업로드 함수
  const uploadFile = async () => {
    if (!file) return; // ✅ 여기서 파일이 null이면 실행되지 않음

    setIsUploading(true); // ✅ 업로드 중 상태 활성화
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:7000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      alert(response.data.message); // ✅ 업로드 완료 메시지
      setFile(null); // ✅ 파일 상태 초기화
    } catch (error) {
      console.error("파일 업로드 오류:", error);
    } finally {
      setIsUploading(false); // ✅ 업로드 상태 해제
    }
  };

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
          </div>
        ))}
        {isLoading && <div className={styles.loadingMessage}>⏳ 응답 생성 중...</div>}
      </div>
        
      {/* 입력 및 버튼 영역 */}
      <div className={`${styles.inputContainer} ${hasMessages ? styles.inputFixed : styles.inputCenter}`}>
        {/* ✅ 파일 업로드 */}
        <div className={styles.uploadContainer}>
          <label htmlFor="file-upload" className={styles.fileLabel}>📂 파일 선택</label>
          <input
            id="file-upload"
            type="file"
            onChange={(e) => {
              const selectedFile = e.target.files?.[0] || null;
              setFile(selectedFile); // ✅ 상태만 업데이트 (즉시 업로드 X)
            }}
            className={styles.fileInput}
          />
          {isUploading && <p className={styles.uploadMessage}>⏳ 파일 업로드 중...</p>} {/* ✅ 업로드 중 로딩 표시 */}
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
