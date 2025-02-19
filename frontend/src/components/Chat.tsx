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

  // ✅ STT 초기화 (Web Speech API)
  useEffect(() => {
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition =
        (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recog = new SpeechRecognition();
      recog.lang = "ko-KR";
      recog.interimResults = false;

      recog.onstart = () => {
        setIsListening(true);
      };

      recog.onend = () => {
        setIsListening(false);
      };

      recog.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript); // 입력창에 텍스트 업데이트
      };

      setRecognition(recog);
    } else {
      console.error("Speech Recognition API not supported in this browser.");
    }
  }, []);

  // ✅ TTS (Text-to-Speech) 함수
  const speak = (text: string) => {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "en-US";
      window.speechSynthesis.speak(utterance);
    } else {
      console.error("Speech Synthesis API not supported in this browser.");
    }
  };

  // ✅ 메시지 전송 함수
  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { role: "user", content: input }];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post("http://127.0.0.1:8000/chat", {
        message: input,
      });

      const updatedMessages = [
        ...newMessages,
        { role: "assistant", content: response.data.response },
      ];
      setMessages(updatedMessages);

      // TTS로 챗봇 응답 읽어주기
      speak(response.data.response);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsLoading(false);  // ✅ 응답 생성 완료 후 로딩 상태 해제
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

  return (
    <div className={styles.chatContainer}>
      <div className={styles.chatHeader}>
        <h2>채팅</h2>
      </div>
      <div className={styles.chatHistory}>
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
      <div className={styles.inputContainer}>
        <input
          type="text"
          className={styles.inputBox}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
        />
        <button onClick={sendMessage} className={styles.sendButton} disabled={isLoading}>
          {isLoading ? "⌛" : "보내기"}
        </button>
        <button onClick={startListening} className={styles.sttButton} disabled={!recognition}>
          {isListening ? "Listening..." : "🎙️"}
        </button>
      </div>
    </div>
  );
}
